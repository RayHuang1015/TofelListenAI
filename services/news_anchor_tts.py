"""
News Anchor TTS Service - Generate professional news anchor audio for daily editions
"""
import os
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from pathlib import Path
import requests
from openai import OpenAI

from app import app, db
from models import DailyEdition, EditionSegment

class NewsAnchorTTS:
    """Generate professional news anchor-style audio for daily news editions"""
    
    # News anchor voice settings
    VOICE_MODELS = {
        'primary': 'alloy',      # Professional female anchor
        'male': 'echo',          # Professional male anchor
        'backup': 'nova'         # Alternative voice
    }
    
    # Audio quality settings
    AUDIO_FORMAT = 'mp3'
    SAMPLE_RATE = 22050
    SPEED = 1.0  # Normal speaking speed
    
    # Duration targets
    TARGET_WORDS_PER_MINUTE = 160  # Professional news anchor pace
    SEGMENT_TARGET_DURATION = 180  # 3 minutes per segment
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.openai_client = self._initialize_openai()
        self.audio_dir = Path('static/audio/news')
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
    def _initialize_openai(self) -> Optional[OpenAI]:
        """Initialize OpenAI client for TTS"""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            self.logger.warning("OPENAI_API_KEY not found - TTS will be disabled")
            return None
        
        try:
            client = OpenAI(api_key=api_key)
            # Test the client with a simple request
            return client
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            return None
    
    def generate_anchor_script(self, headline: str, content: str, duration_target: int = 180) -> str:
        """
        Generate professional news anchor script from headline and content
        
        Args:
            headline: News headline
            content: Original news content
            duration_target: Target duration in seconds
            
        Returns:
            Professional anchor script formatted for TTS
        """
        # Calculate target word count based on speaking pace
        target_words = (duration_target * self.TARGET_WORDS_PER_MINUTE) // 60
        
        # Create anchor-style script template
        script_template = f"""
        Good evening. I'm reporting from our international news desk.
        
        {headline}
        
        {self._format_content_for_anchor(content, target_words - 50)}  # Reserve words for intro/outro
        
        We'll continue following this developing story. 
        This has been your international news update.
        """
        
        return script_template.strip()
    
    def _format_content_for_anchor(self, content: str, target_words: int) -> str:
        """Format content in news anchor style with proper pacing"""
        
        # Clean and split content
        sentences = content.replace('\n', ' ').split('.')
        formatted_sentences = []
        word_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Add news anchor phrasing
            if word_count == 0:
                sentence = f"According to reports, {sentence.lower()}"
            
            # Add appropriate pauses for dramatic effect
            if any(word in sentence.lower() for word in ['breaking', 'urgent', 'crisis', 'emergency']):
                sentence = f"[PAUSE] {sentence} [PAUSE]"
            
            words_in_sentence = len(sentence.split())
            if word_count + words_in_sentence > target_words:
                break
                
            formatted_sentences.append(sentence)
            word_count += words_in_sentence
        
        return '. '.join(formatted_sentences) + '.'
    
    def generate_audio_for_segment(self, segment: EditionSegment, voice: str = 'primary') -> Optional[str]:
        """
        Generate TTS audio for a news segment
        
        Args:
            segment: EditionSegment to generate audio for
            voice: Voice model to use
            
        Returns:
            Path to generated audio file or None if failed
        """
        if not self.openai_client:
            self.logger.error("OpenAI client not initialized - cannot generate audio")
            return None
            
        try:
            # Generate anchor script
            script = self.generate_anchor_script(
                segment.headline,
                segment.transcript_text or segment.headline,
                segment.duration_sec
            )
            
            # Create voice settings
            voice_model = self.VOICE_MODELS.get(voice, self.VOICE_MODELS['primary'])
            
            # Generate audio using OpenAI TTS
            response = self.openai_client.audio.speech.create(
                model="tts-1-hd",  # High quality model
                voice=voice_model,
                input=script,
                response_format=self.AUDIO_FORMAT,
                speed=self.SPEED
            )
            
            # Save audio file
            audio_filename = f"segment_{segment.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{self.AUDIO_FORMAT}"
            audio_path = self.audio_dir / str(segment.edition_id) / audio_filename
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write audio data
            with open(audio_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
            
            # Update segment with audio path
            relative_path = str(audio_path.relative_to(Path('static')))
            segment.segment_metadata = segment.segment_metadata or {}
            if isinstance(segment.segment_metadata, str):
                segment.segment_metadata = json.loads(segment.segment_metadata)
            
            segment.segment_metadata.update({
                'audio_file': relative_path,
                'tts_voice': voice_model,
                'tts_generated_at': datetime.now().isoformat(),
                'anchor_script': script
            })
            
            db.session.commit()
            
            self.logger.info(f"Generated audio for segment {segment.id}: {relative_path}")
            return relative_path
            
        except Exception as e:
            self.logger.error(f"Failed to generate audio for segment {segment.id}: {e}")
            return None
    
    def generate_full_edition_audio(self, edition_id: int) -> Dict[str, Any]:
        """
        Generate complete audio package for a daily edition
        
        Args:
            edition_id: DailyEdition ID
            
        Returns:
            Generation results summary
        """
        with app.app_context():
            try:
                edition = DailyEdition.query.get(edition_id)
                if not edition:
                    return {'status': 'error', 'message': f'Edition {edition_id} not found'}
                
                # Get all segments for this edition
                segments = EditionSegment.query.filter_by(edition_id=edition_id).order_by(EditionSegment.seq).all()
                
                if not segments:
                    return {'status': 'error', 'message': f'No segments found for edition {edition_id}'}
                
                generated_files = []
                failed_segments = []
                total_duration = 0
                
                # Generate audio for each segment
                for i, segment in enumerate(segments):
                    voice = 'primary' if i % 2 == 0 else 'male'  # Alternate voices for variety
                    
                    audio_path = self.generate_audio_for_segment(segment, voice)
                    if audio_path:
                        generated_files.append({
                            'segment_id': segment.id,
                            'audio_path': audio_path,
                            'duration': segment.duration_sec
                        })
                        total_duration += segment.duration_sec
                    else:
                        failed_segments.append(segment.id)
                
                # Update edition metadata
                edition.edition_metadata = edition.edition_metadata or {}
                if isinstance(edition.edition_metadata, str):
                    edition.edition_metadata = json.loads(edition.edition_metadata)
                
                edition.edition_metadata.update({
                    'audio_generated': True,
                    'audio_generation_date': datetime.now().isoformat(),
                    'generated_segments': len(generated_files),
                    'failed_segments': len(failed_segments),
                    'total_audio_duration': total_duration,
                    'audio_files': generated_files
                })
                
                db.session.commit()
                
                return {
                    'status': 'success',
                    'edition_id': edition_id,
                    'generated_segments': len(generated_files),
                    'failed_segments': len(failed_segments),
                    'total_duration': total_duration,
                    'audio_files': generated_files
                }
                
            except Exception as e:
                self.logger.error(f"Failed to generate edition audio for {edition_id}: {e}")
                return {'status': 'error', 'message': str(e)}
    
    def create_news_bulletin_intro(self, date: date) -> str:
        """Create professional news bulletin introduction"""
        return f"""
        Good evening. This is your international news bulletin for {date.strftime('%A, %B %d, %Y')}.
        I'm bringing you the latest developments from around the world.
        Let's begin with tonight's top stories.
        """
    
    def create_news_bulletin_outro(self) -> str:
        """Create professional news bulletin conclusion"""
        return """
        That concludes tonight's international news bulletin.
        Thank you for staying informed with us.
        We'll be back tomorrow with more news from around the world.
        Good night.
        """