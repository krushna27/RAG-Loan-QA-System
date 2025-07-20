from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
import re
import os

class BankOfMaharashtraLoanScraper:
    def __init__(self):
        self.chrome_driver_path = "C:/Users/msi1/Documents/chromedriver-win64/chromedriver.exe"
        self.base_url = "https://bankofmaharashtra.in"
        self.loan_schemes = []
        
        # Define loan categories and their URLs
        self.loan_urls = {
       'personal_loan': 'https://bankofmaharashtra.in/personal-banking/loans/personal-loan',
        'home_loan': 'https://bankofmaharashtra.in/personal-banking/loans/home-loan',
        'gold_loan': 'https://bankofmaharashtra.in/gold-loan'
        }

#method that uses a headless Chrome browser to load a given URL and return its full HTML content.
#  It ensures the page is fully loaded by waiting for the <body> tag to appear

    def get_page(self, url):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        service = Service(self.chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)
            return driver.page_source
        except Exception as e:
            print(f"Error loading {url}: {e}")
            return None
        finally:
            driver.quit()

# parsed HTML page (soup), its URL, and the loan category, then extracts and organizes key loan details—such as the loan name, 
# financial info, eligibility, required documents,
#  features/benefits, tables, and other text sections—into a structured dictionary

    def extract_loan_details(self, soup, url, loan_category):
        try:
            print(f"Extracting all data from: {url}")
            
            # 1. BASIC INFORMATION
            loan_name = self.extract_title(soup, loan_category)
            
            # 2. ALL TEXT CONTENT
            full_text = soup.get_text(separator=' ', strip=True)
            
            # 3. STRUCTURED DATA EXTRACTION
            loan_data = {
                'basic_info': {
                    'name': loan_name,
                    'category': loan_category,
                 
                },
                
                'financial_details': self.extract_financial_info(full_text, soup),
                'eligibility_criteria': self.extract_eligibility(soup, full_text),
                'required_documents': self.extract_documents(soup, full_text),
                'features_benefits': self.extract_features(soup, full_text),
         

                'tables': self.extract_all_tables(soup),
               
                'sections': self.extract_sections(soup),
   
                'raw_content': {
                    'full_text': full_text,
                    'paragraphs': [p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()],
                    'divs': [div.get_text().strip() for div in soup.find_all('div') if div.get_text().strip() and len(div.get_text().strip()) > 20]
                },
            
            }

            return loan_data

        except Exception as e:
            print(f"Error extracting from {url}: {e}")
            return {'error': str(e), 'url': url}
    
    def extract_title(self, soup, loan_category):
        """Extract page title using multiple methods"""
        title_selectors = [
            'h1', 'h2', '.page-title', '.loan-title', '.scheme-title', 
            '.main-title', '.banner-title', 'title', '.heading'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()
        
        return f"{loan_category.replace('_', ' ').title()}"
    # scans the provided text using regular expressions to extract key financial components of a loan scheme:
    def extract_financial_info(self, text, soup):
        """Extract all financial information"""
        financial_info = {}
        
        # Interest rates
        rate_patterns = [
            r'(?:interest rate|roi|rate of interest).*?(\d+\.?\d*%?\s*(?:p\.a\.?|per annum)?)',
            r'(\d+\.?\d*%\s*(?:p\.a\.?|per annum))',
            r'(\d+\.?\d*\s*percent\s*(?:p\.a\.?|per annum)?)'
        ]
        
        rates = []
        for pattern in rate_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            rates.extend(matches)
        financial_info['interest_rates'] = list(set(rates))
        
        # Loan amounts
        amount_patterns = [
            r'(?:maximum|max|up to|loan amount).*?(?:rs\.?|₹)\s*(\d+(?:,\d+)*(?:\.\d+)?\s*(?:lakh|crore)?)',
            r'(?:rs\.?|₹)\s*(\d+(?:,\d+)*\s*(?:lakh|crore))',
            r'(\d+\s*(?:lakh|crore))',
            r'(?:minimum|min).*?(?:rs\.?|₹)\s*(\d+(?:,\d+)*)'
        ]
        
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
        financial_info['loan_amounts'] = list(set(amounts))
        
        # Tenure/Duration
        tenure_patterns = [
            r'(?:tenure|repayment period|loan period|duration).*?(\d+\s*(?:years?|months?))',
            r'(?:up to)\s*(\d+\s*years?)',
            r'(\d+\s*years?\s*tenure)',
            r'(\d+-\d+\s*years?)'
        ]
        
        tenures = []
        for pattern in tenure_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            tenures.extend(matches)
        financial_info['tenure'] = list(set(tenures))
        
        # Processing fees and charges
        fee_patterns = [
            r'(?:processing fee|charges|service charge).*?(?:rs\.?|₹)\s*(\d+(?:,\d+)*)',
            r'(?:processing fee|charges).*?(\d+\.?\d*%)',
            r'(?:nil|no|zero)\s*(?:processing fee|charges)'
        ]
        
        fees = []
        for pattern in fee_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            fees.extend(matches)
        financial_info['fees_charges'] = list(set(fees))
        
        return financial_info
    
    def extract_eligibility(self, soup, text):
        """Extract eligibility criteria"""
        eligibility = {}
        
        # Look for eligibility sections
        eligibility_sections = soup.find_all(['div', 'section'], 
            string=re.compile(r'eligibilit', re.IGNORECASE)) or \
            soup.find_all(['h2', 'h3', 'h4'], 
            string=re.compile(r'eligibilit', re.IGNORECASE))
        
        criteria = []
        for section in eligibility_sections:
            parent = section.parent if section.parent else section
            lists = parent.find_all(['ul', 'ol'])
            for ul in lists:
                items = [li.get_text().strip() for li in ul.find_all('li')]
                criteria.extend(items)
        
        # Age criteria
        age_pattern = r'(?:age|years).*?(\d+.*?\d+.*?years?)'
        age_matches = re.findall(age_pattern, text, re.IGNORECASE)
        
        eligibility['criteria_list'] = criteria
        eligibility['age_requirements'] = age_matches
 
        
        return eligibility
    
    def extract_documents(self, soup, text):
        """Extract required documents"""
        documents = {}
        
        # Look for document sections
        doc_keywords = ['document', 'papers', 'proof', 'certificate']
        doc_sections = []
        
        for keyword in doc_keywords:
            sections = soup.find_all(['div', 'section'], 
                string=re.compile(keyword, re.IGNORECASE))
            doc_sections.extend(sections)
        
        all_docs = []
        for section in doc_sections:
            parent = section.parent if section.parent else section
            lists = parent.find_all(['ul', 'ol'])
            for ul in lists:
                items = [li.get_text().strip() for li in ul.find_all('li')]
                all_docs.extend(items)
        
        documents['required_documents'] = all_docs
        
        
        doc_patterns = [
            r'(pan card|aadhar|passport|driving license)',
            r'(income proof|salary slip|itr)',
            r'(bank statement|passbook)',
            r'(property document|title deed)'
        ]
        
        found_docs = []
        for pattern in doc_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_docs.extend(matches)
        
        documents['identified_documents'] = found_docs
        
        return documents
    
    def extract_features(self, soup, text):
        """Extract features and benefits"""
        features = {}
        
        # Find feature sections
        feature_keywords = ['feature', 'benefit', 'advantage', 'highlight']
        feature_lists = []
        
        for keyword in feature_keywords:
            # Look for headings with these keywords
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'], 
                string=re.compile(keyword, re.IGNORECASE))
            
            for heading in headings:
                # Find next sibling lists
                next_element = heading.find_next_sibling()
                while next_element:
                    if next_element.name in ['ul', 'ol']:
                        items = [li.get_text().strip() for li in next_element.find_all('li')]
                        feature_lists.extend(items)
                        break
                    next_element = next_element.find_next_sibling()

        all_lists = soup.find_all(['ul', 'ol'])
        for ul in all_lists:
            items = [li.get_text().strip() for li in ul.find_all('li')]
            # Filter out very short or very long items
            filtered_items = [item for item in items if 10 < len(item) < 200]
            feature_lists.extend(filtered_items)
        
        features['feature_list'] = list(set(feature_lists))
        
        return features
    
    def extract_all_tables(self, soup):
        """Extract all table data"""
        tables = []
        
        for table in soup.find_all('table'):
            table_data = {
                'headers': [],
                'rows': []
            }
            
            # Extract headers
            headers = table.find_all('th')
            if headers:
                table_data['headers'] = [th.get_text().strip() for th in headers]
            
            # Extract rows
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if cells:
                    row_data = [cell.get_text().strip() for cell in cells]
                    table_data['rows'].append(row_data)
            
            if table_data['rows']:  # Only add non-empty tables
                tables.append(table_data)
        
        return tables
    
    def extract_all_headings(self, soup):
        """Extract all headings"""
        headings = {}
        
        for level in range(1, 7):  # h1 to h6
            heading_tag = f'h{level}'
            headings[heading_tag] = [h.get_text().strip() for h in soup.find_all(heading_tag)]
        
        return headings
    
  
    
    def extract_sections(self, soup):
        """Extract content by sections/divs"""
        sections = []
        
        for section in soup.find_all(['section', 'div', 'article']):
            if section.get('class') or section.get('id'):
                section_data = {
                    'tag': section.name,
                    'class': section.get('class', []),
                    'id': section.get('id', ''),
                    'text': section.get_text().strip()[:500]  # First 500 chars
                }
                if section_data['text']:  # Only non-empty sections
                    sections.append(section_data)
        
        return sections

# scrape_all_loans method systematically loops through all loan URLs, 
# loads each webpage, parses its content, extracts structured loan data, and stores the results
    def scrape_all_loans(self):
        total_urls = len(self.loan_urls)
        
        for i, (loan_category, url) in enumerate(self.loan_urls.items(), 1):
            print(f"\n[{i}/{total_urls}] Scraping {loan_category}...")
            print(f"URL: {url}")
            
            page_source = self.get_page(url)
            if not page_source:
                print(f"❌ Failed to load page: {url}")
                continue

            soup = BeautifulSoup(page_source, 'html.parser')
            print("📄 Page loaded successfully, extracting all data...")
            
            loan_details = self.extract_loan_details(soup, url, loan_category)
            
            if loan_details and 'error' not in loan_details:
                self.loan_schemes.append(loan_details)
                print(f"✅ Successfully scraped: {loan_details['basic_info']['name']}")
                print(f"   - Found {len(loan_details.get('tables', []))} tables")
                print(f"   - Found {len(loan_details.get('lists', {}).get('unordered_lists', []))} lists")
                print(f"   - Found {len(loan_details.get('links', []))} links")
                print(f"   - Extracted {len(loan_details.get('raw_content', {}).get('paragraphs', []))} paragraphs")
            else:
                print(f"❌ Failed to extract data from: {url}")
                if 'error' in loan_details:
                    print(f"   Error: {loan_details['error']}")
            
            print(f"⏳ Waiting 3 seconds before next request...")
            time.sleep(3)  # Respectful delay

        return self.loan_schemes

    def save_to_txt(self, filename='scraped_data_mahaloan2.txt'):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("BANK OF MAHARASHTRA LOAN SCHEMES - COMPLETE DATA\n")
            f.write("=" * 80 + "\n\n")
            
            for i, loan in enumerate(self.loan_schemes, 1):
                if 'error' in loan:
                    f.write(f"SCHEME {i}: ERROR\n")
                    f.write(f"URL: {loan.get('url', 'Unknown')}\n")
                    f.write(f"Error: {loan['error']}\n")
                    f.write("-" * 80 + "\n\n")
                    continue
                
                basic = loan.get('basic_info', {})
                f.write(f"SCHEME {i}: {basic.get('name', 'Unknown Scheme')}\n")
                f.write("=" * 60 + "\n")
                f.write(f"Category: {basic.get('category', 'N/A')}\n")
              
                
                # Financial Details
                financial = loan.get('financial_details', {})
                if any(financial.values()):
                    f.write("FINANCIAL DETAILS:\n")
                    f.write("-" * 30 + "\n")
                    if financial.get('interest_rates'):
                        f.write(f"Interest Rates: {', '.join(financial['interest_rates'])}\n")
                    if financial.get('loan_amounts'):
                        f.write(f"Loan Amounts: {', '.join(financial['loan_amounts'])}\n")
                    if financial.get('tenure'):
                        f.write(f"Tenure: {', '.join(financial['tenure'])}\n")
                    if financial.get('fees_charges'):
                        f.write(f"Fees & Charges: {', '.join(financial['fees_charges'])}\n")
                    f.write("\n")
                
                # Eligibility
                eligibility = loan.get('eligibility_criteria', {})
                if any(eligibility.values()):
                    f.write("ELIGIBILITY CRITERIA:\n")
                    f.write("-" * 30 + "\n")
                    if eligibility.get('age_requirements'):
                        f.write(f"Age Requirements: {', '.join(eligibility['age_requirements'])}\n")
                    if eligibility.get('criteria_list'):
                        f.write("Criteria:\n")
                        for criteria in eligibility['criteria_list'][:10]:  # Limit to 10
                            f.write(f"  • {criteria}\n")
                    f.write("\n")
                
                # Required Documents
                documents = loan.get('required_documents', {})
                if any(documents.values()):
                    f.write("REQUIRED DOCUMENTS:\n")
                    f.write("-" * 30 + "\n")
                    if documents.get('required_documents'):
                        for doc in documents['required_documents'][:15]:  # Limit to 15
                            f.write(f"  • {doc}\n")
                    if documents.get('identified_documents'):
                        f.write(f"Common Documents: {', '.join(documents['identified_documents'])}\n")
                    f.write("\n")
                
                # Features & Benefits
                features = loan.get('features_benefits', {})
                if features.get('feature_list'):
                    f.write("FEATURES & BENEFITS:\n")
                    f.write("-" * 30 + "\n")
                    for feature in features['feature_list'][:20]:  # Limit to 20
                        f.write(f"  • {feature}\n")
                    f.write("\n")
                
                # Tables
                tables = loan.get('tables', [])
                if tables:
                    f.write("TABLES DATA:\n")
                    f.write("-" * 30 + "\n")
                    for j, table in enumerate(tables, 1):
                        f.write(f"Table {j}:\n")
                        if table.get('headers'):
                            f.write(f"Headers: {' | '.join(table['headers'])}\n")
                        for row in table.get('rows', [])[:10]:  # Limit rows
                            f.write(f"  {' | '.join(row)}\n")
                        f.write("\n")
                
                # All Headings
                headings = loan.get('headings', {})
                if any(headings.values()):
                    f.write("PAGE HEADINGS:\n")
                    f.write("-" * 30 + "\n")
                    for level, heading_list in headings.items():
                        if heading_list:
                            f.write(f"{level.upper()}: {', '.join(heading_list)}\n")
                    f.write("\n")
            
                raw_content = loan.get('raw_content', {})
                if raw_content.get('paragraphs'):
                    f.write("KEY PARAGRAPHS:\n")
                    f.write("-" * 30 + "\n")
                    for para in raw_content['paragraphs'][:10]:  # Limit to 10 paragraphs
                        if len(para) > 50:  # Only meaningful paragraphs
                            f.write(f"  • {para[:200]}{'...' if len(para) > 200 else ''}\n")
                    f.write("\n")
               
        
        print(f"Complete data saved to {filename}")
        print(f"File size: {os.path.getsize(filename) / 1024:.1f} KB")

if __name__ == "__main__":
    scraper = BankOfMaharashtraLoanScraper("chromedriver.exe")
    
    loans = scraper.scrape_all_loans()
    
    scraper.save_to_txt()
    
    print(f"Scraping completed! Total schemes: {len(loans)}")
    print("All data saved file")