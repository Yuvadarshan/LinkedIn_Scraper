import csv
import re
import urllib.parse
from supabase import create_client, Client
import parameters
import uuid

class ProfileURLEnhancer:
    def __init__(self):
        self.supabase = None
        
    def setup_supabase(self):
        """Setup Supabase connection"""
        try:
            print("🗄️ Connecting to Supabase...")
            self.supabase: Client = create_client(parameters.SUPABASE_URL, parameters.SUPABASE_KEY)
            print("✅ Supabase connected")
            return True
        except Exception as e:
            print(f"❌ Supabase error: {e}")
            return False
    
    def generate_targeted_search_urls(self, profile_data):
        """Generate targeted LinkedIn search URLs for each profile"""
        enhanced_profiles = []
        
        for i, profile in enumerate(profile_data):
            try:
                title = profile.get('title', '').strip()
                location = profile.get('location', '').strip()
                
                # Skip if no meaningful data
                if not title:
                    continue
                
                # Handle case where location equals title (common in our data)
                if location == title:
                    location = ''
                
                print(f"\n👤 Profile {i+1}: {title}")
                
                enhanced_profile = {
                    'original_title': title,
                    'original_location': location,
                    'name': '',
                    'headline': title,
                    'location': location if location != title else '',
                    'profile_url': '',
                    'search_urls': []
                }
                
                # Extract potential name and role
                name_match = self.extract_name_from_title(title)
                if name_match:
                    enhanced_profile['name'] = name_match
                    print(f"   👤 Extracted name: {name_match}")
                
                # Generate multiple targeted search URLs
                search_urls = []
                
                # 1. Direct name + CIT search
                if enhanced_profile['name']:
                    name_search = f"{enhanced_profile['name']} Chennai Institute of Technology"
                    search_urls.append({
                        'type': 'name_search',
                        'url': f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(name_search)}",
                        'description': f"Search for {enhanced_profile['name']} at CIT"
                    })
                
                # 2. Role + CIT search
                role_keywords = self.extract_role_keywords(title)
                if role_keywords:
                    role_search = f"{role_keywords} Chennai Institute of Technology"
                    search_urls.append({
                        'type': 'role_search',
                        'url': f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(role_search)}",
                        'description': f"Search for {role_keywords} at CIT"
                    })
                
                # 3. Location-specific search
                if location and location != title:
                    location_search = f"Chennai Institute of Technology {location}"
                    search_urls.append({
                        'type': 'location_search',
                        'url': f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(location_search)}",
                        'description': f"Search for CIT profiles in {location}"
                    })
                
                # 4. Google search for LinkedIn profile
                if enhanced_profile['name']:
                    google_search = f"site:linkedin.com/in \"{enhanced_profile['name']}\" \"Chennai Institute of Technology\""
                    search_urls.append({
                        'type': 'google_search',
                        'url': f"https://www.google.com/search?q={urllib.parse.quote(google_search)}",
                        'description': f"Google search for {enhanced_profile['name']}'s LinkedIn profile"
                    })
                
                enhanced_profile['search_urls'] = search_urls
                enhanced_profiles.append(enhanced_profile)
                
                print(f"   🔍 Generated {len(search_urls)} targeted search URLs")
                
            except Exception as e:
                print(f"   ❌ Error processing profile: {e}")
                continue
        
        return enhanced_profiles
    
    def extract_name_from_title(self, title):
        """Extract potential name from title"""
        try:
            # Remove common institutional terms
            cleaned = re.sub(r'\b(at|of|the|in|and|&)\b', ' ', title, flags=re.IGNORECASE)
            cleaned = re.sub(r'\b(Chennai Institute of Technology|CIT|Chennai|Technology|Institute)\b', ' ', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\b(Professor|Assistant|Associate|Student|Principal|Faculty|Director|Dean)\b', ' ', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\b(Attended|Studying|Graduated|Alumni)\b', ' ', cleaned, flags=re.IGNORECASE)
            
            # Clean up whitespace
            cleaned = ' '.join(cleaned.split())
            
            # Look for potential names (2-4 words, mostly alphabetic)
            words = cleaned.split()
            name_words = []
            
            for word in words:
                if (len(word) > 1 and 
                    word.isalpha() and 
                    word[0].isupper() and
                    word.lower() not in ['the', 'and', 'or', 'at', 'in', 'of']):
                    name_words.append(word)
            
            if 2 <= len(name_words) <= 4:
                return ' '.join(name_words)
            
            return None
            
        except:
            return None
    
    def extract_role_keywords(self, title):
        """Extract role keywords from title"""
        try:
            role_patterns = [
                r'\b(Assistant Professor|Associate Professor|Professor)\b',
                r'\b(Principal|Director|Dean|Faculty|Lecturer)\b',
                r'\b(Student|Graduate|Alumni|Scholar)\b',
                r'\b(Engineer|Developer|Analyst|Manager)\b'
            ]
            
            for pattern in role_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            return None
            
        except:
            return None
    
    def create_enhanced_csv(self, enhanced_profiles):
        """Create enhanced CSV with targeted search URLs"""
        filename = "cit_alumni_enhanced_with_search_urls.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'name', 'headline', 'location', 'profile_url', 
                    'name_search_url', 'role_search_url', 'location_search_url', 
                    'google_search_url', 'search_descriptions'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for profile in enhanced_profiles:
                    search_urls = profile.get('search_urls', [])
                    
                    # Extract specific search URLs
                    name_search_url = ''
                    role_search_url = ''
                    location_search_url = ''
                    google_search_url = ''
                    descriptions = []
                    
                    for search in search_urls:
                        if search['type'] == 'name_search':
                            name_search_url = search['url']
                        elif search['type'] == 'role_search':
                            role_search_url = search['url']
                        elif search['type'] == 'location_search':
                            location_search_url = search['url']
                        elif search['type'] == 'google_search':
                            google_search_url = search['url']
                        
                        descriptions.append(f"{search['type']}: {search['description']}")
                    
                    writer.writerow({
                        'name': profile.get('name', ''),
                        'headline': profile.get('headline', ''),
                        'location': profile.get('location', ''),
                        'profile_url': '',  # To be filled when real URLs are found
                        'name_search_url': name_search_url,
                        'role_search_url': role_search_url,
                        'location_search_url': location_search_url,
                        'google_search_url': google_search_url,
                        'search_descriptions': ' | '.join(descriptions)
                    })
            
            print(f"💾 Enhanced CSV saved as {filename}")
            print(f"📄 Contains targeted search URLs for finding real LinkedIn profiles")
            return filename
            
        except Exception as e:
            print(f"❌ Error creating enhanced CSV: {e}")
            return None
    
    def create_manual_search_guide(self, enhanced_profiles):
        """Create a manual search guide"""
        filename = "manual_linkedin_search_guide.html"
        
        try:
            html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>CIT Alumni LinkedIn Search Guide</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .profile { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .profile h3 { color: #0077b5; margin-top: 0; }
        .search-link { display: inline-block; margin: 5px; padding: 8px 12px; background: #0077b5; color: white; text-decoration: none; border-radius: 3px; }
        .search-link:hover { background: #005885; }
        .instructions { background: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>🎯 CIT Alumni LinkedIn Profile Search Guide</h1>
    
    <div class="instructions">
        <h2>📋 How to Use This Guide:</h2>
        <ol>
            <li><strong>Click on the search links below</strong> to open targeted LinkedIn searches</li>
            <li><strong>Look through the search results</strong> for the specific person</li>
            <li><strong>When you find the real profile</strong>, copy the actual LinkedIn URL (should look like: https://linkedin.com/in/username)</li>
            <li><strong>Replace the generic URLs</strong> in your database with the real profile URLs</li>
        </ol>
        <p><em>💡 Tip: Use the Google search links to find profiles that might not show up in LinkedIn search</em></p>
    </div>
    
"""
            
            for i, profile in enumerate(enhanced_profiles):
                name = profile.get('name', 'Unknown')
                headline = profile.get('headline', 'No headline')
                location = profile.get('location', 'No location')
                
                html_content += f"""
    <div class="profile">
        <h3>👤 Profile {i+1}: {name if name else headline}</h3>
        <p><strong>Headline:</strong> {headline}</p>
        <p><strong>Location:</strong> {location}</p>
        
        <div>
            <strong>🔍 Search Links:</strong><br>
"""
                
                for search in profile.get('search_urls', []):
                    html_content += f'            <a href="{search["url"]}" target="_blank" class="search-link">{search["description"]}</a><br>\n'
                
                html_content += """        </div>
        
        <div style="margin-top: 10px;">
            <label><strong>✏️ Real LinkedIn URL:</strong></label>
            <input type="text" style="width: 400px; margin-left: 10px;" placeholder="Paste the real LinkedIn profile URL here">
        </div>
    </div>
"""
            
            html_content += """
</body>
</html>
"""
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"📄 Manual search guide created: {filename}")
            print(f"🌐 Open this HTML file in your browser to start finding real LinkedIn URLs")
            return filename
            
        except Exception as e:
            print(f"❌ Error creating search guide: {e}")
            return None
    
    def update_database_with_placeholders(self, enhanced_profiles):
        """Update database with enhanced profile data"""
        try:
            if not self.supabase:
                print("⚠️ Supabase not connected")
                return 0
            
            # Clear existing data
            print("🧹 Clearing existing data...")
            try:
                self.supabase.table(parameters.SUPABASE_TABLE).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            except:
                pass
            
            saved_count = 0
            for profile in enhanced_profiles:
                try:
                    supabase_data = {
                        'profile_id': str(uuid.uuid4()),
                        'name': profile.get('name', profile.get('headline', 'Unknown'))[:100],
                        'profile_url': '[TO_BE_UPDATED]'  # Placeholder for real URL
                    }
                    
                    if profile.get('location'):
                        supabase_data['location'] = profile['location'][:100]
                    
                    if profile.get('headline'):
                        supabase_data['about'] = profile['headline'][:200]
                    
                    # Add search URLs as notes
                    search_notes = []
                    for search in profile.get('search_urls', [])[:2]:  # First 2 search URLs
                        search_notes.append(f"{search['type']}: {search['url']}")
                    
                    if search_notes:
                        supabase_data['skills'] = ' | '.join(search_notes)[:300]
                    
                    result = self.supabase.table(parameters.SUPABASE_TABLE).insert(supabase_data).execute()
                    if result.data:
                        saved_count += 1
                        
                except Exception as e:
                    print(f"⚠️ Error saving profile: {e}")
                    continue
            
            print(f"🗄️ Updated database with {saved_count} enhanced profiles")
            return saved_count
            
        except Exception as e:
            print(f"❌ Database update error: {e}")
            return 0
    
    def run_enhancement(self):
        """Run the profile URL enhancement"""
        try:
            print("🎯 CIT Alumni Profile URL Enhancer")
            print("=" * 50)
            
            self.setup_supabase()
            
            # Read existing CSV data
            existing_data = []
            try:
                with open('cit_alumni_manual.csv', 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    existing_data = list(reader)
                print(f"📄 Loaded {len(existing_data)} profiles from existing CSV")
            except Exception as e:
                print(f"❌ Error reading existing CSV: {e}")
                return
            
            # Enhance profile data
            enhanced_profiles = self.generate_targeted_search_urls(existing_data)
            
            if enhanced_profiles:
                print(f"\n📊 Enhancement Results:")
                print(f"✅ Enhanced {len(enhanced_profiles)} profiles")
                
                # Create outputs
                csv_filename = self.create_enhanced_csv(enhanced_profiles)
                guide_filename = self.create_manual_search_guide(enhanced_profiles)
                
                # Update database
                saved_count = self.update_database_with_placeholders(enhanced_profiles)
                
                print(f"\n🎉 ENHANCEMENT COMPLETED!")
                print(f"📄 Enhanced CSV: {csv_filename}")
                print(f"🌐 Search Guide: {guide_filename}")
                print(f"🗄️ Database entries: {saved_count}")
                print(f"\n📋 Next Steps:")
                print(f"1. Open {guide_filename} in your browser")
                print(f"2. Use the search links to find real LinkedIn profiles")
                print(f"3. Copy the real profile URLs and update your database")
                print(f"4. Each profile now has multiple targeted search strategies!")
                
                return enhanced_profiles
                
            else:
                print("😞 No profiles could be enhanced")
                return []
                
        except Exception as e:
            print(f"❌ Enhancement error: {e}")
            return []

def main():
    print("🚀 CIT Alumni Profile URL Enhancer")
    print("🔍 Creating targeted search strategies for real LinkedIn URLs")
    print("=" * 70)
    
    enhancer = ProfileURLEnhancer()
    
    try:
        profiles = enhancer.run_enhancement()
        
        if profiles:
            print(f"\n🎊 SUCCESS!")
            print(f"✅ Enhanced {len(profiles)} profiles with targeted search URLs")
            print(f"🔍 Each profile now has multiple search strategies")
            print(f"📋 Use the HTML guide to find real LinkedIn profile URLs")
            print(f"💡 This approach will help you get the actual profile URLs you need!")
        else:
            print("\n😞 No profiles enhanced")
        
    except KeyboardInterrupt:
        print("\n🛑 Enhancement stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
