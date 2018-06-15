from flask import Flask, Response, render_template, request,jsonify, redirect
import json
from wtforms import TextField, Form
import requests
from spellcheck import correct
from operator import itemgetter
import re
from bs4 import BeautifulSoup
from bs4.element import Comment
import nltk

app = Flask(__name__)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search = request.args.get('q').lower()
    r = json.loads(requests.get("http://localhost:8983/solr/myexample/suggest?q="+search).content)
    r = r['suggest']['suggest']
    terms = []
    for i in r[search]["suggestions"]:
        terms.append(i["term"])

    return jsonify(matching_results=terms)




def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    #page = soup.find('p').getText()
    return u" ".join(t.strip() for t in visible_texts)
    #return page

@app.route('/search', methods = ['POST'])
def signup():
    query = request.form['autocomplete']
    radio = request.form["algorithm"]
    print "radio", radio
    print("Query Term '" + query + "'")
    isCorrected = False
    new_query = []
    for q in query.lower().split(" "):
        corrected = correct(q)
        if corrected == q:
            continue
        else:
            isCorrected = True
        new_query.append(corrected)
    if isCorrected:
        new_query = " ".join(new_query)
        query = new_query
    print new_query
    if radio=="pagerank":
        r=json.loads(requests.get("http://localhost:8983/solr/myexample/select?q="+query+"&sort=pageRankFile%20desc").content)
    else:
        r = json.loads(requests.get("http://localhost:8983/solr/myexample/select?q="+query).content)
    r = r['response']
    print r
    result =[]
    for doc in r['docs'][:10]:
        data = doc["id"]
        with open(data) as f:
            text = text_from_html(f.read())

        print text
        q_terms = [query]+query.split()
        text = " ".join(re.split("\s+",text))
        data = nltk.sent_tokenize(text)

        snippet = ""
        found = False
        for d in q_terms:
            for s in data:
                if d.lower() in s.lower():
                    # l = s.lower().find(d.lower)
                    snippet = s#.lower().replace(d.lower(),"<b>"+d+"</b>")
                    found = True
                    break
            if found:
                break
        dicto = {}
        dicto['title'] = doc['title'][0]
        #dicto['description'] = doc['description']
        #dicto['id'] = doc['id']
        if snippet!="":
            # if l<20:
            #     start=0
            # start = l-20
            # end = l+140
            snippet = snippet[0:160]

        if "og_url" in doc:
            dicto['url'] = doc['og_url'][0]
        else:
            dicto['url'] = ""
        if snippet == "" and 'description' in doc:
            dicto['snippet'] = doc['description'][0]
        elif 'description' not in doc and snippet=="" or snippet!="":
            dicto['snippet'] = snippet
        result.append(dicto)


    return render_template('search.html', new_query=new_query, results=result,display=True,query=query,display_new=isCorrected)




@app.route('/', methods=['GET', 'POST'])
def index():
    #form = SearchForm(request.form)
    return render_template("search.html",display=False)

if __name__ == '__main__':
    app.run(debug=True)
