import urllib.request
from datetime import date

# Get today date
today = date.today()
date = today.strftime("%Y-%m-%d")

# Get corresponding Almanax
almanax_url = "http://www.krosmoz.com/fr/almanax/" + date
fp = urllib.request.urlopen(almanax_url)
html = fp.read()
text = html.decode("utf8")
fp.close()
for line in text.split('\n'):
    if 'Récupérer' in line:
        offrande = line
        break

fp.close()
offrande = offrande[15:-17]
offrande += "\nhttps://www.krosmoz.com/fr/almanax"