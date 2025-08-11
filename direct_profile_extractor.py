from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import parameters
from supabase import create_client, Client
import uuid
import re
import random

class DirectProfileExtractor:
    def __init__(self):
        self.driver = None
        self.supabase = None
        self.extracted_profiles = []
        
    def setup_browser(self):
        """Setup browser with enhanced stealth"""
        try:
            print("🚀 Setting up stealth browser...")
            
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute script to avoid detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)
            
            print("✅ Stealth browser setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
    
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
    
    def linkedin_login(self):
        """Login to LinkedIn with delay"""
        try:
            print("🔐 Logging into LinkedIn...")
            self.driver.get("https://www.linkedin.com/login")
            
            # Random delay to appear human-like
            time.sleep(random.uniform(3, 6))
            
            # Enter credentials slowly
            username_field = self.driver.find_element(By.ID, "username")
            for char in parameters.username:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(random.uniform(1, 2))
            
            password_field = self.driver.find_element(By.ID, "password")
            for char in parameters.password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(random.uniform(1, 2))
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            print("⏳ Waiting for login to complete...")
            time.sleep(random.uniform(8, 12))
            
            current_url = self.driver.current_url
            if "feed" in current_url or "mynetwork" in current_url or "/in/" in current_url:
                print("✅ LinkedIn login successful")
                return True
            else:
                print("⚠️ Login status unclear, continuing anyway...")
                return True
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def search_and_collect_profile_links(self, search_term):
        """Search and collect actual profile links"""
        try:
            profiles = []
            
            # Navigate to people search
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={search_term.replace(' ', '%20')}"
            print(f"🔍 Searching: {search_term}")
            self.driver.get(search_url)
            
            time.sleep(random.uniform(5, 8))
            
            # Scroll to load more results
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))
            
            # Find all profile containers
            search_results = self.driver.find_elements(
                By.CSS_SELECTOR, 
                '.entity-result, .search-result, [data-view-name="search-entity-result-universal-template"]'
            )
            
            print(f"🔍 Found {len(search_results)} search results")
            
            for i, result in enumerate(search_results[:10]):  # Process first 10 results
                try:
                    print(f"\n👤 Processing result {i+1}:")
                    
                    # Get the result text
                    result_text = result.text.strip()
                    
                    # Check if this is CIT-related
                    if not any(keyword in result_text.lower() for keyword in [
                        'chennai institute of technology',
                        'chennai institute technology',
                        'cit chennai'
                    ]):
                        print(f"   ❌ Not CIT-related, skipping")
                        continue
                    
                    # Extract profile information
                    lines = [line.strip() for line in result_text.split('\n') if line.strip()]
                    
                    profile = {}
                    
                    # Find headline
                    for line in lines:
                        if any(keyword in line.lower() for keyword in [
                            'chennai institute of technology',
                            'chennai institute technology'
                        ]):
                            profile['headline'] = line
                            print(f"   📝 Headline: {line}")
                            break
                    
                    # Find name (usually the first non-"LinkedIn Member" line)
                    for line in lines:
                        if (line != "LinkedIn Member" and 
                            line != profile.get('headline', '') and
                            not any(keyword in line.lower() for keyword in [
                                'connections', 'mutual', 'message', 'connect', 'view'
                            ])):
                            profile['name'] = line
                            print(f"   👤 Name: {line}")
                            break
                    
                    # Find location
                    for line in lines:
                        if any(loc in line.lower() for loc in [
                            'coimbatore', 'chennai', 'tamil nadu', 'india'
                        ]):
                            if line != profile.get('headline', '') and line != profile.get('name', ''):
                                profile['location'] = line
                                print(f"   📍 Location: {line}")
                                break
                    
                    # Now try to extract the actual profile URL
                    profile_url = self.extract_profile_url_from_result(result)
                    if profile_url:
                        profile['profile_url'] = profile_url
                        print(f"   🔗 Real URL: {profile_url}")
                    else:
                        profile['profile_url'] = ""
                        print(f"   ⚠️ No real URL found")
                    
                    if 'headline' in profile:
                        profiles.append(profile)
                        print(f"   ✅ Profile added")
                    
                    # Random delay between results
                    time.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    print(f"   ❌ Error processing result {i+1}: {e}")
                    continue
            
            return profiles
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def extract_profile_url_from_result(self, result_element):
        """Extract actual profile URL from a search result"""
        try:
            # Multiple strategies to find profile links
            
            # Strategy 1: Look for links with /in/ in href
            links = result_element.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
            for link in links:
                href = link.get_attribute('href')
                if href and 'linkedin.com/in/' in href:
                    # Clean the URL
                    match = re.search(r'linkedin\.com/in/([^/?]+)', href)
                    if match:
                        username = match.group(1)
                        clean_url = f"https://www.linkedin.com/in/{username}/"
                        return clean_url
            
            # Strategy 2: Look for any clickable elements and check their href
            all_links = result_element.find_elements(By.TAG_NAME, 'a')
            for link in all_links:
                href = link.get_attribute('href')
                if href and '/in/' in href and 'linkedin.com' in href:
                    match = re.search(r'linkedin\.com/in/([^/?]+)', href)
                    if match:
                        username = match.group(1)
                        clean_url = f"https://www.linkedin.com/in/{username}/"
                        return clean_url
            
            # Strategy 3: Click and navigate (risky but sometimes necessary)
            try:
                # Find the main profile link (usually the name or title)
                title_links = result_element.find_elements(By.CSS_SELECTOR, 
                    '.entity-result__title-text a, .search-result__title a, [data-control-name*="profile"] a')
                
                if title_links:
                    main_link = title_links[0]
                    
                    # Store current URL
                    current_url = self.driver.current_url
                    
                    # Click the link
                    self.driver.execute_script("arguments[0].click();", main_link)
                    time.sleep(random.uniform(3, 5))
                    
                    # Check if we're on a profile page
                    new_url = self.driver.current_url
                    if '/in/' in new_url and new_url != current_url:
                        # Extract the clean profile URL
                        match = re.search(r'linkedin\.com/in/([^/?]+)', new_url)
                        if match:
                            username = match.group(1)
                            clean_url = f"https://www.linkedin.com/in/{username}/"
                            
                            # Go back to search results
                            self.driver.back()
                            time.sleep(random.uniform(2, 4))
                            
                            return clean_url
                    
                    # Go back if we didn't find a profile
                    self.driver.back()
                    time.sleep(random.uniform(2, 4))
                    
            except Exception as nav_error:
                print(f"   ⚠️ Navigation method failed: {nav_error}")
                try:
                    self.driver.back()
                    time.sleep(2)
                except:
                    pass
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ URL extraction error: {e}")
            return None
    
    def save_enhanced_results(self, all_profiles):
        """Save results with real LinkedIn URLs"""
        try:
            # Remove duplicates
            unique_profiles = []
            seen_urls = set()
            seen_names = set()
            
            for profile in all_profiles:
                profile_url = profile.get('profile_url', '').strip()
                name = profile.get('name', '').strip()
                
                if profile_url and profile_url not in seen_urls:
                    seen_urls.add(profile_url)
                    unique_profiles.append(profile)
                elif not profile_url and name and name not in seen_names:
                    seen_names.add(name)
                    unique_profiles.append(profile)
            
            # Save to CSV
            filename = "cit_alumni_with_real_profile_urls.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'headline', 'profile_url', 'location']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for profile in unique_profiles:
                    writer.writerow({
                        'name': profile.get('name', profile.get('headline', 'Unknown')),
                        'headline': profile.get('headline', ''),
                        'profile_url': profile.get('profile_url', ''),
                        'location': profile.get('location', '')
                    })
            
            print(f"💾 Saved {len(unique_profiles)} unique profiles to {filename}")
            
            # Save to Supabase
            if self.supabase:
                print("🗄️ Clearing existing data...")
                try:
                    self.supabase.table(parameters.SUPABASE_TABLE).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                except:
                    pass
                
                saved_count = 0
                for profile in unique_profiles:
                    try:
                        supabase_data = {
                            'profile_id': str(uuid.uuid4()),
                            'name': profile.get('name', profile.get('headline', 'Unknown'))[:100],
                            'profile_url': profile.get('profile_url', '')[:500]
                        }
                        
                        if profile.get('location'):
                            supabase_data['location'] = profile['location'][:100]
                        
                        if profile.get('headline'):
                            supabase_data['about'] = profile['headline'][:200]
                        
                        result = self.supabase.table(parameters.SUPABASE_TABLE).insert(supabase_data).execute()
                        if result.data:
                            saved_count += 1
                            
                    except Exception as e:
                        print(f"⚠️ Error saving profile to database: {e}")
                        continue
                
                print(f"🗄️ Saved {saved_count} profiles to Supabase")
            
            return unique_profiles
            
        except Exception as e:
            print(f"❌ Save error: {e}")
            return []
    
    def run_direct_extraction(self):
        """Run direct profile extraction with real URLs"""
        try:
            print("🎯 CIT Alumni Direct Profile URL Extractor")
            print("=" * 55)
            
            if not self.setup_browser():
                return []
            
            self.setup_supabase()
            
            if not self.linkedin_login():
                print("⚠️ Login failed, stopping...")
                return []
            
            # Wait after login
            time.sleep(random.uniform(3, 6))
            
            # Search queries for comprehensive results
            search_queries = [
                "Chennai Institute of Technology student",
                "Chennai Institute of Technology professor",
                "Chennai Institute of Technology alumni", 
                "CIT Chennai",
                "Chennai Institute Technology faculty"
            ]
            
            all_profiles = []
            
            for query in search_queries:
                try:
                    profiles = self.search_and_collect_profile_links(query)
                    if profiles:
                        all_profiles.extend(profiles)
                        print(f"✅ Found {len(profiles)} profiles for: {query}")
                    else:
                        print(f"❌ No profiles found for: {query}")
                    
                    # Delay between searches
                    time.sleep(random.uniform(5, 10))
                    
                except Exception as e:
                    print(f"❌ Error with query '{query}': {e}")
                    continue
            
            # Process and save results
            if all_profiles:
                unique_profiles = self.save_enhanced_results(all_profiles)
                
                print(f"\n📊 FINAL RESULTS:")
                print(f"✅ Collected {len(unique_profiles)} unique CIT alumni")
                
                # Count profiles with real URLs
                profiles_with_urls = len([p for p in unique_profiles if p.get('profile_url')])
                print(f"🔗 {profiles_with_urls} profiles have real LinkedIn URLs")
                
                # Display sample results
                print(f"\n🎯 Sample Results with Real URLs:")
                for i, profile in enumerate(unique_profiles[:5]):
                    name = profile.get('name', 'N/A')
                    url = profile.get('profile_url', 'No URL')
                    headline = profile.get('headline', 'N/A')
                    
                    print(f"  {i+1}. Name: {name}")
                    print(f"     Real LinkedIn URL: {url}")
                    print(f"     Headline: {headline}")
                    print()
                
                print(f"🎉 EXTRACTION COMPLETED!")
                print(f"📄 Check 'cit_alumni_with_real_profile_urls.csv' for complete list")
                print(f"🗄️ Database updated with real profile URLs")
                
                return unique_profiles
                
            else:
                print("\n😞 No profiles collected")
                return []
                
        except Exception as e:
            print(f"❌ Extraction error: {e}")
            return []
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print("🧹 Browser closed")
                except:
                    pass

def main():
    print("🚀 CIT Alumni Direct Profile URL Extractor")
    print("🔗 Extracting REAL LinkedIn profile URLs")
    print("=" * 60)
    
    extractor = DirectProfileExtractor()
    
    try:
        profiles = extractor.run_direct_extraction()
        
        if profiles:
            real_url_count = len([p for p in profiles if p.get('profile_url')])
            print(f"\n🎊 SUCCESS!")
            print(f"✅ Total profiles: {len(profiles)}")
            print(f"🔗 Profiles with real URLs: {real_url_count}")
            print(f"📊 Success rate: {(real_url_count/len(profiles)*100):.1f}%")
            print(f"💾 All data saved with actual LinkedIn profile URLs!")
        else:
            print("\n😞 No profiles extracted")
        
    except KeyboardInterrupt:
        print("\n🛑 Extraction stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
