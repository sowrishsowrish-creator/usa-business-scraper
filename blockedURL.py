'''
Sowrish Sithanathan
Data Scraper
June 8 2026
Blocked URLs
'''

# big directory / review / roundup sites - skip these results entirely
# since they arent the actual small business
noURL = [
    "yelp.com", 
    "yellowpages.com",
    "angi.com", 
    "thumbtack.com",
    "tripadvisor.com", 
    "facebook.com", 
    "instagram.com", 
    "linkedin.com",
    "bbb.org", 
    "manta.com", 
    "mapquest.com", 
    "foursquare.com",
    "groupon.com", 
    "nextdoor.com", 
    "niche.com", 
    "chamberofcommerce.com",
    "indeed.com", 
    "glassdoor.com", 
    "wikipedia.org", 
    "youtube.com",
    "reddit.com", 
    "pinterest.com", 
    "twitter.com", 
    "x.com",
    "expertise.com", 
    "threebestrated.com", 
    "birdeye.com", 
    "google.com", 
    "ecorp.sos.ga.gov", 
    "sos.ga.gov", 
    "booksy.com", 
    "engima.com",
    "gbj.com",
    "houzz.com",
    "seolium.com",
    "local.yahoo.com",
    "cbsnews.com",
    "gbd.georgia.gov",
]