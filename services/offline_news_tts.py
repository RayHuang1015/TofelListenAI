"""
Offline News Anchor TTS Service - Generate professional news anchor audio without API keys
Uses pyttsx3 (built-in) and StyleTTS2 for high-quality offline text-to-speech
"""
import os
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from pathlib import Path
import tempfile
import subprocess

from app import app, db
from models import DailyEdition, EditionSegment

class OfflineNewsAnchorTTS:
    """Generate professional news anchor-style audio using offline TTS engines"""
    
    # Voice settings for different TTS engines
    PYTTSX3_VOICES = {
        'professional_female': {'rate': 160, 'volume': 0.9},
        'professional_male': {'rate': 155, 'volume': 0.9},
        'news_anchor': {'rate': 165, 'volume': 1.0}
    }
    
    # Audio settings
    AUDIO_FORMAT = 'wav'
    TARGET_WORDS_PER_MINUTE = 160  # Professional news anchor pace
    SEGMENT_TARGET_DURATION = 180  # 3 minutes per segment
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.audio_dir = Path('static/audio/news')
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize TTS engines
        self.pyttsx3_engine = self._init_pyttsx3()
        self.styletts2_available = self._check_styletts2()
        
    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine with news anchor settings"""
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            
            # Set professional news anchor voice settings
            voices = engine.getProperty('voices')
            if voices:
                # Prefer female voice for news anchor (usually more professional)
                for voice in voices:
                    if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
                else:
                    # Fallback to first available voice
                    engine.setProperty('voice', voices[0].id)
            
            # Set professional speaking rate and volume
            engine.setProperty('rate', 160)  # Words per minute
            engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
            
            self.logger.info("pyttsx3 TTS engine initialized successfully")
            return engine
            
        except Exception as e:
            self.logger.error(f"Failed to initialize pyttsx3: {e}")
            return None
    
    def _check_styletts2(self) -> bool:
        """Check if StyleTTS2 is available"""
        # Temporarily disable StyleTTS2 due to large model download causing worker crashes
        self.logger.info("StyleTTS2 disabled to avoid worker crashes, using pyttsx3 only")
        return False
    
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
        
        # Create anchor-style script with proper pacing
        intro_words = "Good evening from our international news desk."
        
        # Format headline for professional delivery
        formatted_headline = f"Breaking news: {headline}"
        if not headline.endswith('.'):
            formatted_headline += "."
        
        # Process content for news anchor delivery
        formatted_content = self._format_content_for_anchor(content, target_words - 25)  # Reserve words for intro/outro
        
        outro_words = "We will continue monitoring this developing story. This has been your international news update."
        
        # Combine with proper pauses
        script = f"{intro_words} {formatted_headline} {formatted_content} {outro_words}"
        
        return script.strip()
    
    def _format_content_for_anchor(self, content: str, target_words: int) -> str:
        """Format content in news anchor style with proper pacing"""
        
        if not content:
            return "Details are still developing and will be provided as they become available."
        
        # Clean and split content
        content = content.replace('\n', ' ').replace('\r', ' ')
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        
        formatted_sentences = []
        word_count = 0
        
        for i, sentence in enumerate(sentences):
            if not sentence:
                continue
            
            # Add news anchor phrasing for first sentence
            if i == 0 and not sentence.lower().startswith(('according to', 'reports indicate', 'sources confirm')):
                sentence = f"According to reports, {sentence.lower()}"
            
            # Add emphasis for key terms
            if any(word in sentence.lower() for word in ['breaking', 'urgent', 'crisis', 'emergency']):
                sentence = f"In a developing situation, {sentence.lower()}"
            
            # Check word count
            words_in_sentence = len(sentence.split())
            if word_count + words_in_sentence > target_words:
                break
                
            formatted_sentences.append(sentence)
            word_count += words_in_sentence
        
        result = '. '.join(formatted_sentences)
        if result and not result.endswith('.'):
            result += '.'
            
        return result or "Details are developing and updates will follow."
    
    def generate_audio_with_pyttsx3(self, text: str, output_path: str) -> bool:
        """Generate audio using pyttsx3 (offline)"""
        if not self.pyttsx3_engine:
            return False
            
        try:
            # Save to temporary file first, then move to final location
            temp_path = str(output_path) + ".tmp"
            
            self.pyttsx3_engine.save_to_file(text, temp_path)
            self.pyttsx3_engine.runAndWait()
            
            # Move temp file to final location
            if os.path.exists(temp_path):
                os.rename(temp_path, output_path)
                return True
            else:
                self.logger.error(f"pyttsx3 failed to create audio file: {temp_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"pyttsx3 audio generation failed: {e}")
            return False
    
    def generate_audio_with_styletts2(self, text: str, output_path: str) -> bool:
        """Generate high-quality audio using StyleTTS2 (offline)"""
        if not self.styletts2_available:
            return False
            
        try:
            from styletts2 import tts
            
            # Initialize StyleTTS2 (downloads model on first use, then offline)
            my_tts = tts.StyleTTS2()
            
            # Generate audio
            result = my_tts.inference(text, output_wav_file=output_path)
            
            if os.path.exists(output_path):
                self.logger.info(f"StyleTTS2 generated audio: {output_path}")
                return True
            else:
                self.logger.error("StyleTTS2 failed to create audio file")
                return False
                
        except Exception as e:
            self.logger.error(f"StyleTTS2 audio generation failed: {e}")
            return False
    
    def generate_audio_for_segment(self, segment: EditionSegment, quality: str = 'standard') -> Optional[str]:
        """
        Generate TTS audio for a news segment
        
        Args:
            segment: EditionSegment to generate audio for
            quality: 'standard' (pyttsx3) or 'high' (StyleTTS2)
            
        Returns:
            Path to generated audio file or None if failed
        """
        try:
            # Generate anchor script
            script = self.generate_anchor_script(
                segment.headline,
                segment.transcript_text or segment.headline,
                segment.duration_sec
            )
            
            # Create audio filename
            audio_filename = f"segment_{segment.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{self.AUDIO_FORMAT}"
            audio_path = self.audio_dir / str(segment.edition_id) / audio_filename
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Try high-quality first if requested, then fallback to standard
            success = False
            tts_engine_used = "unknown"
            
            if quality == 'high' and self.styletts2_available:
                success = self.generate_audio_with_styletts2(script, str(audio_path))
                tts_engine_used = "StyleTTS2"
                
            if not success:
                # Fallback to pyttsx3
                success = self.generate_audio_with_pyttsx3(script, str(audio_path))
                tts_engine_used = "pyttsx3"
            
            if not success:
                self.logger.error(f"All TTS engines failed for segment {segment.id}")
                return None
            
            # Update segment with audio path
            relative_path = str(audio_path.relative_to(Path('static')))
            
            # Handle segment metadata
            if segment.segment_metadata is None:
                segment.segment_metadata = {}
            elif isinstance(segment.segment_metadata, str):
                segment.segment_metadata = json.loads(segment.segment_metadata)
            
            segment.segment_metadata.update({
                'audio_file': relative_path,
                'tts_engine': tts_engine_used,
                'tts_generated_at': datetime.now().isoformat(),
                'anchor_script': script,
                'audio_quality': quality
            })
            
            db.session.commit()
            
            self.logger.info(f"Generated {quality} quality audio for segment {segment.id} using {tts_engine_used}: {relative_path}")
            return relative_path
            
        except Exception as e:
            self.logger.error(f"Failed to generate audio for segment {segment.id}: {e}")
            return None
    
    def generate_full_edition_audio(self, edition_id: int, quality: str = 'standard') -> Dict[str, Any]:
        """
        Generate complete audio package for a daily edition
        
        Args:
            edition_id: DailyEdition ID
            quality: 'standard' or 'high'
            
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
                for segment in segments:
                    audio_path = self.generate_audio_for_segment(segment, quality)
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
                if edition.edition_metadata is None:
                    edition.edition_metadata = {}
                elif isinstance(edition.edition_metadata, str):
                    edition.edition_metadata = json.loads(edition.edition_metadata)
                
                edition.edition_metadata.update({
                    'audio_generated': True,
                    'audio_generation_date': datetime.now().isoformat(),
                    'generated_segments': len(generated_files),
                    'failed_segments': len(failed_segments),
                    'total_audio_duration': total_duration,
                    'audio_quality': quality,
                    'audio_files': generated_files
                })
                
                db.session.commit()
                
                return {
                    'status': 'success',
                    'edition_id': edition_id,
                    'generated_segments': len(generated_files),
                    'failed_segments': len(failed_segments),
                    'total_duration': total_duration,
                    'audio_quality': quality,
                    'audio_files': generated_files
                }
                
            except Exception as e:
                self.logger.error(f"Failed to generate edition audio for {edition_id}: {e}")
                return {'status': 'error', 'message': str(e)}
    
    def test_tts_engines(self) -> Dict[str, Any]:
        """Test available TTS engines"""
        results = {
            'pyttsx3': {'available': False, 'test_result': None},
            'styletts2': {'available': False, 'test_result': None}
        }
        
        # Test pyttsx3
        if self.pyttsx3_engine:
            try:
                test_file = self.audio_dir / "test_pyttsx3.wav"
                success = self.generate_audio_with_pyttsx3("This is a test of the pyttsx3 news anchor voice.", str(test_file))
                results['pyttsx3'] = {
                    'available': True, 
                    'test_result': 'success' if success else 'failed',
                    'test_file': str(test_file) if success else None
                }
            except Exception as e:
                results['pyttsx3']['test_result'] = f"error: {e}"
        
        # Test StyleTTS2
        if self.styletts2_available:
            try:
                test_file = self.audio_dir / "test_styletts2.wav"
                success = self.generate_audio_with_styletts2("This is a test of the StyleTTS2 high-quality news anchor voice.", str(test_file))
                results['styletts2'] = {
                    'available': True,
                    'test_result': 'success' if success else 'failed', 
                    'test_file': str(test_file) if success else None
                }
            except Exception as e:
                results['styletts2']['test_result'] = f"error: {e}"
        
        return results