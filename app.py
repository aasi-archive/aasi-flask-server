# This is a search server
# Configure the URL where it is hosted on in ./build/config.json

# Send a JSON post request to this route: /api/search on the server to query various texts.
# The query format is simple,
# {
#   "text": "<SCRIPTURE CODE>" (supported: 'MBH' for Mahabharata, 'RMY' for Ramayana),
#   "query": "<A regular expression query"
# }

# Here is how it works
# First the text is condensed into a JSON with
# "<Book>:<Canto>": "<Content>"
# And then this server returns the JSON with the following
# "start": "<Book>:<Canto>"
# "surrounding": "... text <div class="query_match">matched part</div>..."

from flask import Flask, request, abort, jsonify
from flask_cors import CORS, cross_origin
import json
import re
import sys
from easygoogletranslate import EasyGoogleTranslate

MAX_RESULTS = 100
SURROUNDING_CHARS_MAX = 30 

def run_query_on_index(index, query):
    total_results = 0 
    results = {}
    regx = re.compile(query, flags=re.DOTALL|re.MULTILINE)
    for section in index.keys():
        if(total_results > MAX_RESULTS):
            break
        n = len(index[section])
        for mtch in regx.finditer(index[section]):
            results[section] = {}
            results[section]["start"] = mtch.start()
            pre_match_start = mtch.start() - SURROUNDING_CHARS_MAX
            pre_match_end = mtch.start()

            post_match_start = mtch.start() + len(mtch.group())
            post_match_end =  post_match_start + SURROUNDING_CHARS_MAX

            if(pre_match_start < 0):
                pre_match_start = 0
                pre_match_end = mtch.start()

            if(post_match_start > n):
                post_match_start = n - SURROUNDING_CHARS_MAX
                post_match_end = n - 1

            results[section]["surrounding"] = "..." + index[section][pre_match_start:pre_match_end]  + '<span class="query_match">' + mtch.group() + '</span>' + index[section][post_match_start:post_match_end] + "..."
            total_results += 1
    return results

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

with open('mbh.json', 'r') as f:
    mbh_search_index = json.loads(f.read())
    f.close()

@app.route("/api/search", methods=['POST'])
@cross_origin()
def search_result():
    query = request.json
    results = {}
    if(query['text'] == 'MBH'):
        results = run_query_on_index(mbh_search_index, query['query'])
    else:
        abort(404)

    return jsonify(results)

@app.route("/api/translate", methods=['POST'])
def return_translation():
    query = request.json
    if('sl' not in query or 'tl' not in query or 'text' not in query):
        abort(403)

    if(len(query['text']) > 5000):
        return jsonify({"text": "Google Translate API character limit exceeded." })
    
    try:
        translator = EasyGoogleTranslate(query['sl'], query['tl'], 5)
        return jsonify({"text": translator.translate(query['text']) })
    except:
        return jsonify({"text": "An unexpected error occurred."})
    
if __name__ == "__main__":
    app.run(debug=True)
