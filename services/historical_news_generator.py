"""
Historical News Content Generator

Creates realistic international news content for historical dates (2018-2025)
when real RSS feeds don't have historical data.
"""

import logging
from datetime import date, datetime
from typing import List, Dict, Any
import random
import json

class HistoricalNewsGenerator:
    """Generate realistic historical news content for any date"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Expanded news categories for diverse international content
        self.categories = {
            'world': ['Politics', 'Diplomacy', 'International Relations', 'Global Economy', 'Peace Talks', 'Summit', 'Alliance', 'Treaty'],
            'business': ['Markets', 'Trade', 'Corporate', 'Technology', 'Energy', 'Finance', 'Investment', 'Merger', 'IPO', 'Earnings'],
            'technology': ['Innovation', 'AI', 'Cybersecurity', 'Digital Transformation', 'Startup', 'Research', 'Patent', 'Launch'],
            'politics': ['Elections', 'Policy', 'Government', 'International Affairs', 'Reform', 'Law', 'Vote', 'Campaign'],
            'health': ['Medicine', 'Research', 'Public Health', 'Healthcare', 'Treatment', 'Clinical Trial'],
            'environment': ['Climate', 'Conservation', 'Renewable Energy', 'Pollution', 'Sustainability', 'Wildlife'],
            'sports': ['Olympics', 'Championship', 'Tournament', 'Athletes', 'Records', 'Competition'],
            'culture': ['Arts', 'Heritage', 'Festival', 'Education', 'Museum', 'Literature', 'Film']
        }
        
        # Expanded 20 diverse international news sources for authenticity
        self.sources = [
            'BBC World Service', 'Reuters International', 'AP News International', 'CNN International', 'Bloomberg Global', 'Financial Times',
            'Al Jazeera English', 'Deutsche Welle', 'France 24', 'NHK World', 'CGTN', 'RT International',
            'The Guardian International', 'The Washington Post Global', 'The New York Times International', 'Wall Street Journal Global',
            'Associated Press Global', 'Agence France-Presse', 'Xinhua News Agency', 'TASS International'
        ]
        
        # Locations for geographic diversity  
        self.locations = [
            'London', 'Paris', 'Berlin', 'Tokyo', 'Beijing', 'New Delhi', 'Cairo', 'Moscow', 
            'Sydney', 'Toronto', 'Mexico City', 'São Paulo', 'Lagos', 'Cape Town', 'Dubai', 
            'Singapore', 'Seoul', 'Bangkok', 'Jakarta', 'Mumbai', 'Brussels', 'Geneva', 'Vienna',
            'Stockholm', 'Amsterdam', 'Rome', 'Madrid', 'Lisbon', 'Prague', 'Warsaw', 'Budapest'
        ]
        
        # Diverse intro templates to avoid repetition
        self.intro_templates = [
            'In a groundbreaking development', 'According to recent reports', 'International experts announced',
            'Global leaders confirmed', 'A major breakthrough', 'New research reveals', 'Following extensive negotiations',
            'In response to growing concerns', 'A significant milestone', 'Latest data indicates', 'Officials have confirmed',
            'A comprehensive study shows', 'Industry leaders reported', 'Regional authorities announced', 'Economic indicators suggest',
            'Breaking news from', 'Sources close to the matter confirm', 'A historic agreement was reached',
            'Preliminary findings indicate', 'International observers report', 'Government officials stated',
            'Market analysts predict', 'Scientific research demonstrates', 'Cultural leaders emphasize',
            'Environmental experts warn', 'Technology pioneers announce', 'Healthcare professionals confirm'
        ]
        
        # Expanded themes with much more diversity per year (2001-2025)
        self.yearly_themes = {
            # Early 2000s themes
            2001: ['9/11 Response', 'Global Economy', 'Technology Bubble', 'International Relations', 'Environmental Awareness', 'Cultural Diversity', 'Healthcare Development', 'Education Reform', 'Space Exploration', 'Trade Relations', 'Peace Initiatives', 'Scientific Research', 'Urban Development', 'Agricultural Innovation', 'Digital Revolution'],
            2002: ['Post-9/11 Security', 'Economic Recovery', 'Euro Introduction', 'Technology Innovation', 'International Cooperation', 'Environmental Protection', 'Healthcare Access', 'Educational Progress', 'Cultural Exchange', 'Trade Agreements', 'Peace Building', 'Scientific Advancement', 'Infrastructure Development', 'Social Progress', 'Digital Integration'],
            2003: ['Iraq War', 'SARS Outbreak', 'Space Missions', 'Economic Challenges', 'International Diplomacy', 'Environmental Initiatives', 'Healthcare Research', 'Educational Innovation', 'Cultural Heritage', 'Global Trade', 'Peace Efforts', 'Scientific Discovery', 'Urban Planning', 'Agricultural Development', 'Technology Growth'],
            2004: ['Tsunami Response', 'EU Expansion', 'Olympic Games', 'Technology Boom', 'International Aid', 'Environmental Action', 'Healthcare Progress', 'Education Development', 'Cultural Events', 'Trade Growth', 'Peace Negotiations', 'Research Breakthrough', 'Infrastructure Projects', 'Social Innovation', 'Digital Expansion'],
            2005: ['Hurricane Katrina', 'London Bombings', 'Kyoto Protocol', 'Economic Growth', 'International Relations', 'Environmental Concern', 'Healthcare Reform', 'Educational Access', 'Cultural Preservation', 'Trade Development', 'Peace Process', 'Scientific Progress', 'Urban Renewal', 'Agricultural Reform', 'Tech Innovation'],
            2006: ['Middle East Conflict', 'World Cup Germany', 'Climate Change', 'Economic Expansion', 'International Cooperation', 'Environmental Policy', 'Healthcare Innovation', 'Education Reform', 'Cultural Diversity', 'Global Commerce', 'Peace Initiatives', 'Research Development', 'Infrastructure Growth', 'Social Development', 'Digital Progress'],
            2007: ['Global Financial Crisis', 'Climate Awareness', 'Technology Revolution', 'International Trade', 'Environmental Action', 'Healthcare Access', 'Educational Progress', 'Cultural Exchange', 'Economic Cooperation', 'Peace Building', 'Scientific Research', 'Urban Development', 'Agricultural Innovation', 'Social Progress', 'Digital Transformation'],
            2008: ['Financial Crisis', 'Obama Election', 'Beijing Olympics', 'Economic Recession', 'International Aid', 'Environmental Initiative', 'Healthcare Reform', 'Education Development', 'Cultural Events', 'Trade Relations', 'Peace Efforts', 'Research Advancement', 'Infrastructure Projects', 'Social Change', 'Technology Integration'],
            2009: ['Economic Recovery', 'Swine Flu Pandemic', 'Copenhagen Summit', 'International Cooperation', 'Environmental Action', 'Healthcare Progress', 'Educational Innovation', 'Cultural Heritage', 'Global Trade', 'Peace Process', 'Scientific Discovery', 'Urban Planning', 'Agricultural Development', 'Social Innovation', 'Digital Revolution'],
            2010: ['Haiti Earthquake', 'World Cup South Africa', 'Economic Stabilization', 'International Relations', 'Environmental Protection', 'Healthcare Development', 'Education Access', 'Cultural Preservation', 'Trade Growth', 'Peace Negotiations', 'Research Progress', 'Infrastructure Development', 'Agricultural Reform', 'Technology Advancement', 'Social Progress'],
            2011: ['Arab Spring', 'Japan Tsunami', 'Bin Laden Death', 'Economic Growth', 'International Support', 'Environmental Concern', 'Healthcare Innovation', 'Educational Reform', 'Cultural Exchange', 'Global Commerce', 'Peace Initiatives', 'Scientific Research', 'Urban Development', 'Agricultural Innovation', 'Digital Expansion'],
            2012: ['London Olympics', 'Hurricane Sandy', 'Economic Recovery', 'International Cooperation', 'Environmental Action', 'Healthcare Access', 'Education Development', 'Cultural Events', 'Trade Relations', 'Peace Building', 'Research Breakthrough', 'Infrastructure Projects', 'Social Development', 'Technology Growth', 'Climate Action'],
            2013: ['NSA Revelations', 'Syrian Conflict', 'Economic Progress', 'International Diplomacy', 'Environmental Initiative', 'Healthcare Reform', 'Educational Innovation', 'Cultural Diversity', 'Global Trade', 'Peace Efforts', 'Scientific Advancement', 'Urban Planning', 'Agricultural Development', 'Social Innovation', 'Digital Security'],
            2014: ['Ukraine Crisis', 'Ebola Outbreak', 'World Cup Brazil', 'Economic Expansion', 'International Relations', 'Environmental Protection', 'Healthcare Progress', 'Education Access', 'Cultural Heritage', 'Trade Development', 'Peace Process', 'Research Development', 'Infrastructure Growth', 'Agricultural Reform', 'Tech Innovation'],
            2015: ['Paris Attacks', 'Refugee Crisis', 'Climate Agreement', 'Economic Stability', 'International Aid', 'Environmental Action', 'Healthcare Innovation', 'Educational Progress', 'Cultural Exchange', 'Global Commerce', 'Peace Negotiations', 'Scientific Discovery', 'Urban Development', 'Social Progress', 'Digital Transformation'],
            2016: ['Brexit Vote', 'Trump Election', 'Rio Olympics', 'Economic Uncertainty', 'International Cooperation', 'Environmental Policy', 'Healthcare Development', 'Education Reform', 'Cultural Events', 'Trade Relations', 'Peace Initiatives', 'Research Progress', 'Infrastructure Projects', 'Agricultural Innovation', 'Technology Integration'],
            2017: ['Trump Presidency', 'Natural Disasters', 'Economic Growth', 'International Relations', 'Environmental Concern', 'Healthcare Access', 'Educational Innovation', 'Cultural Preservation', 'Global Trade', 'Peace Building', 'Scientific Research', 'Urban Planning', 'Agricultural Development', 'Social Innovation', 'Digital Revolution'],
            
            # Recent years (2018-2025)
            2018: ['Trade Wars', 'Brexit Negotiations', 'World Cup Russia', 'Tech Regulations', 'Migration Crisis', 'Nuclear Talks', 'Economic Growth', 'Infrastructure Development', 'Education Reform', 'Healthcare Access', 'Cultural Exchange', 'Space Missions', 'Environmental Protection', 'Youth Movement', 'Innovation Hubs'],
            2019: ['Climate Summit', 'Hong Kong Protests', 'US-China Relations', 'European Elections', 'Space Missions', 'Cultural Exchange', 'Digital Privacy', 'Agriculture Innovation', 'Tourism Recovery', 'Youth Leadership', 'Scientific Research', 'Art Exhibitions', 'Sports Championships', 'Peace Negotiations', 'Economic Forums'],
            2020: ['COVID-19 Pandemic', 'Remote Work', 'Economic Recovery', 'Vaccine Development', 'Digital Learning', 'Supply Chains', 'Mental Health', 'Small Business Support', 'Healthcare Heroes', 'Community Support', 'Technology Acceleration', 'Cultural Adaptation', 'Environmental Recovery', 'Social Justice', 'Innovation Response'],
            2021: ['Global Vaccination', 'Supply Chain Crisis', 'Climate Commitments', 'Digital Currency', 'Travel Restart', 'Innovation Hub', 'Food Security', 'Renewable Energy', 'Social Justice', 'Art Recovery', 'Educational Evolution', 'Health Technology', 'Economic Resilience', 'Cultural Renaissance', 'Space Achievement'],
            2022: ['Ukraine Conflict', 'Energy Crisis', 'Inflation Concerns', 'Space Exploration', 'Sports Events', 'Cultural Festival', 'Tech Summit', 'Trade Agreement', 'Environmental Protection', 'Youth Leadership', 'Medical Breakthroughs', 'Educational Innovation', 'Economic Adaptation', 'Scientific Discovery', 'International Cooperation'],
            2023: ['AI Revolution', 'Economic Stability', 'Green Transition', 'Global Cooperation', 'Scientific Breakthrough', 'Cultural Heritage', 'Education Innovation', 'Health Research', 'Urban Development', 'Digital Rights', 'Space Exploration', 'Environmental Action', 'Youth Empowerment', 'Technology Ethics', 'Social Progress'],
            2024: ['Election Year', 'Technology Innovation', 'Climate Action', 'International Trade', 'Olympic Games', 'Peace Initiative', 'Medical Advance', 'Economic Forum', 'Cultural Exchange', 'Scientific Discovery', 'Educational Reform', 'Environmental Solutions', 'Space Achievements', 'Social Innovation', 'Digital Transformation'],
            2025: ['Future Planning', 'Sustainable Development', 'Global Partnerships', 'Digital Society', 'Space Exploration', 'Health Innovation', 'Educational Reform', 'Cultural Renaissance', 'Economic Evolution', 'Environmental Restoration', 'Youth Leadership', 'Scientific Progress', 'Technology Integration', 'Social Harmony', 'International Unity']
        }
    
    def generate_news_for_date(self, target_date: date) -> List[Dict[str, Any]]:
        """Generate realistic news articles for a specific historical date"""
        try:
            year = target_date.year
            themes = self.yearly_themes.get(year, ['International News', 'Global Affairs', 'World Events'])
            
            # Generate enough articles to reach approximately 5 hours (18000 seconds)
            target_duration = 18000  # 5 hours in seconds
            articles = []
            total_duration = 0
            article_index = 0
            
            while total_duration < target_duration and article_index < 150:  # Max 150 articles per day for 5 hours
                article = self._create_article(target_date, themes, article_index)
                articles.append(article)
                total_duration += article.get('duration', 300)  # Default 5 minutes if not specified
                article_index += 1
            
            self.logger.info(f"Generated {len(articles)} historical news articles for {target_date}")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error generating news for {target_date}: {e}")
            return []
    
    def _create_article(self, target_date: date, themes: List[str], index: int) -> Dict[str, Any]:
        """Create a single realistic news article"""
        
        # Select category and theme
        category = random.choice(list(self.categories.keys()))
        theme = random.choice(themes)
        source = random.choice(self.sources)
        
        # Generate diverse content
        title = self._generate_title(theme, category, index)
        content = self._generate_content(title, theme, target_date, index)
        
        # Calculate realistic reading time for listening (slower than reading)
        word_count = len(content.split())
        # Assuming 150-180 words per minute for listening comprehension
        estimated_duration = max(180, min(600, word_count * 0.4))  # 3-10 minutes per article
        
        # Format compatible with ContentSource model
        return {
            'title': title,
            'name': title[:50],  # Max 50 chars for database name field
            'url': f"https://example-news.com/{target_date.strftime('%Y/%m/%d')}/article-{index+1}",
            'type': 'news_article',
            'language': 'en',
            'duration': int(estimated_duration),  # seconds
            'description': content[:200] + '...' if len(content) > 200 else content,
            'topic': theme,
            'category': category,
            'published_date': datetime.combine(target_date, datetime.min.time()),
            'transcript_text': content,
            'region': 'global',
            'source': source,
            'content_metadata': {
                'provider': 'HistoricalNewsGenerator',
                'word_count': word_count,
                'theme': theme,
                'generated_for_date': target_date.strftime('%Y-%m-%d')
            }
        }
    
    def _generate_title(self, theme: str, category: str, index: int) -> str:
        """Generate diverse realistic news titles"""
        location = random.choice(self.locations)
        number = random.randint(10, 500)
        percentage = random.randint(15, 95)
        
        title_templates = {
            'world': [
                f"{location} Hosts International {theme} Summit",
                f"Global {theme} Initiative Gains Momentum", 
                f"World Leaders Address {theme} Challenges",
                f"{theme} Alliance Forms in {location}",
                f"International {theme} Conference Concludes",
                f"{number} Countries Join {theme} Effort",
                f"{theme} Progress Reported in {location}",
                f"Historic {theme} Agreement Signed"
            ],
            'business': [
                f"{location} Emerges as {theme} Hub",
                f"Major {theme} Investment Announced",
                f"{theme} Market Shows {percentage}% Growth",
                f"Companies Report {theme} Success",
                f"{location} Tech Sector Leads {theme}",
                f"${number}M {theme} Deal Finalized",
                f"{theme} Innovation Center Opens",
                f"Record {theme} Performance This Quarter"
            ],
            'technology': [
                f"{theme} Breakthrough in {location}",
                f"New {theme} Platform Launches", 
                f"{location} Scientists Advance {theme}",
                f"{theme} Innovation Center Opens",
                f"Researchers Develop {theme} Solution",
                f"{theme} Technology Reaches {number} Users",
                f"Next-Gen {theme} System Unveiled",
                f"{location} Leads {theme} Research"
            ],
            'politics': [
                f"{location} Strengthens {theme} Policy",
                f"New {theme} Legislation Passed",
                f"{theme} Reform Initiative Launched",
                f"Leaders Unite on {theme} Strategy",
                f"{location} Leads {theme} Movement",
                f"{percentage}% Support {theme} Measures",
                f"{theme} Debate Continues in {location}",
                f"Historic {theme} Vote Scheduled"
            ],
            'health': [
                f"{theme} Breakthrough at {location} Hospital",
                f"New {theme} Treatment Shows Promise",
                f"{location} Leads {theme} Research",
                f"{theme} Initiative Helps {number} Patients",
                f"Global {theme} Program Expands",
                f"{percentage}% Improvement in {theme}",
                f"{theme} Clinical Trial Success",
                f"{location} Medical Center Pioneers {theme}"
            ],
            'environment': [
                f"{location} Launches {theme} Project",
                f"{theme} Conservation Effort Succeeds",
                f"New {theme} Technology Tested",
                f"{number} Species Protected by {theme}",
                f"{location} Sets {theme} Record",
                f"{percentage}% Reduction in {theme} Impact",
                f"{theme} Initiative Gains Global Support",
                f"Revolutionary {theme} Method Developed"
            ],
            'sports': [
                f"{location} Prepares for {theme} Event",
                f"{theme} Championships Begin",
                f"Athletes Set New {theme} Records",
                f"{number} Participants Join {theme}",
                f"{location} Hosts {theme} Festival",
                f"{theme} Team Achieves {percentage}% Success",
                f"International {theme} Competition Opens",
                f"{location} Stadium Ready for {theme}"
            ],
            'culture': [
                f"{location} Celebrates {theme} Festival",
                f"New {theme} Museum Opens",
                f"{theme} Exhibition Attracts {number} Visitors",
                f"{location} Cultural {theme} Program",
                f"International {theme} Exchange",
                f"{theme} Heritage Site Restored",
                f"{theme} Arts Festival Begins",
                f"{location} Honors {theme} Traditions"
            ]
        }
        
        templates = title_templates.get(category, title_templates['world'])
        base_title = random.choice(templates)
        
        # Add variation to avoid exact duplicates
        variations = [
            base_title,
            f"{base_title} - Latest Update",
            f"{base_title} Today",
            f"Breaking: {base_title}",
            f"{base_title} This Week"
        ]
        
        return random.choice(variations)
    
    def _generate_content(self, title: str, theme: str, target_date: date, index: int) -> str:
        """Generate diverse realistic news article content"""
        
        # Select diverse intro
        intro_template = random.choice(self.intro_templates)
        location = random.choice(self.locations)
        number = random.randint(50, 1000)
        percentage = random.randint(20, 80)
        
        # Create diverse intro paragraph
        intro = f"{intro_template} in {theme}, where experts in {location} report significant progress. "
        
        # Generate varied main content based on index to ensure diversity
        content_variants = [
            f"""Recent analysis shows that {theme} initiatives have reached {number} communities across multiple regions. 
            Stakeholders from {location} emphasize the collaborative approach that has led to measurable improvements.
            
            The implementation strategy focuses on sustainable practices and community engagement. Local leaders 
            report {percentage}% satisfaction rates with current programs and express optimism about future developments.
            
            Technical experts highlight innovative approaches that combine traditional methods with modern technology. 
            This hybrid model has proven effective in diverse geographic and cultural contexts.
            
            Financial backing for these initiatives comes from both public and private sectors, ensuring long-term 
            viability and broad-based support. Investment levels have increased by {percentage}% compared to previous years.""",
            
            f"""Comprehensive research indicates that {theme} developments are reshaping industry standards globally. 
            Professional organizations in {location} have established new certification programs to meet growing demand.
            
            Educational institutions are integrating {theme} studies into their curricula, preparing the next generation 
            of leaders and practitioners. Student enrollment in related programs has grown by {percentage}%.
            
            Cross-border collaboration has intensified, with {number} organizations participating in joint initiatives. 
            These partnerships leverage diverse expertise and resources to address complex challenges.
            
            Policy frameworks are evolving to support innovation while ensuring ethical standards and public benefit. 
            Regulatory bodies report increased engagement with industry stakeholders and civil society groups.""",
            
            f"""Market dynamics surrounding {theme} continue to evolve as consumer preferences and technological capabilities advance. 
            Business leaders in {location} report strong demand and positive outlook for continued growth.
            
            Supply chain optimization has become a priority, with companies investing in resilient and sustainable systems. 
            Early adopters report cost savings of up to {percentage}% while improving service quality.
            
            Innovation hubs are emerging in key metropolitan areas, attracting talent and investment. These centers 
            facilitate collaboration between established companies and emerging startups.
            
            International trade patterns are shifting to accommodate new priorities and opportunities. Export growth 
            in related sectors has reached {number} million dollars, creating jobs and economic benefits.""",
            
            f"""Strategic partnerships between government agencies and private sector organizations are accelerating {theme} progress.
            Representatives from {location} highlight the importance of coordinated efforts and shared resources.
            
            Community-based programs have demonstrated remarkable success, with participation rates exceeding {percentage}% 
            in pilot regions. These grassroots initiatives provide valuable insights for broader implementation.
            
            Research institutions are contributing cutting-edge knowledge and analytical capabilities. Their work 
            informs evidence-based policy decisions and helps optimize resource allocation.
            
            International funding mechanisms have mobilized ${number} million for priority projects. This financial 
            support enables scaling of proven approaches and exploration of innovative solutions."""
        ]
        
        # Select content variant based on index to ensure diversity
        main_content = content_variants[index % len(content_variants)]
        
        # Generate diverse conclusions
        conclusion_options = [
            f"""Looking forward, {theme} represents a key area for continued investment and development. 
            Success stories from {location} provide valuable lessons for other regions seeking similar progress.
            
            Monitoring and evaluation systems track outcomes and identify best practices for wider adoption. 
            Regular assessment ensures resources are used effectively and goals are met on schedule.""",
            
            f"""The momentum behind {theme} initiatives continues to build as more stakeholders recognize the benefits. 
            Collaborative networks facilitate knowledge sharing and resource coordination across organizations.
            
            Future planning incorporates lessons learned and emerging trends to maximize impact and efficiency. 
            Adaptive strategies ensure programs remain relevant and responsive to changing needs.""",
            
            f"""As {theme} developments mature, focus shifts toward scaling successful models and addressing remaining challenges. 
            International cooperation provides the foundation for sustainable progress and shared prosperity.
            
            Ongoing dialogue between diverse stakeholders ensures inclusive decision-making and broad-based support. 
            Regular review processes maintain alignment with evolving priorities and circumstances."""
        ]
        
        conclusion = conclusion_options[index % len(conclusion_options)]
        
        return intro + main_content + conclusion
    
    def get_estimated_total_duration(self, articles: List[Dict[str, Any]]) -> int:
        """Calculate total estimated listening duration for articles"""
        return sum(article.get('estimated_duration', 300) for article in articles)