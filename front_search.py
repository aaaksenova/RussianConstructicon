import re
import random
import sqlite3
import pymorphy2
import nltk
import streamlit as st
import time
# nltk.download('punkt')

morph = pymorphy2.MorphAnalyzer()
con = sqlite3.connect('constr.db')
POS_TAGS = {'ADJ': 'Adj',
            'ADP': 'Prep',
            'ADV': 'Adv',
            'AUX': 'Verb',
            'CCONJ': 'Cconj',
            'DET': 'Pron',
            'INTJ': 'Intj',
            'NOUN': 'Noun',
            'NUM': 'Num',
            'PART': 'Part',
            'PRON': 'PronPers',
            'PROPN': 'Noun',
            'PUNCT': 'Punct',
            'SCONJ': 'Sconj',
            'SYM': 'Symb',
            'VERB': 'Verb',
            'X': 'X'}

POS_ATTRS = {'Sing': 'Sg',
             'Plur': 'Pl',
             'Imp': 'Ipfv',
             'Perf': 'Pfv',
             'Fut': 'Fut',
             'Past': 'Pst',
             'Pres': 'Pres'}

def get_all_types(construction):
    constructions = []
    constructions.append([construction])
    new = []
    if '(' in construction:
        constructions.append([re.sub(r'\(.+?\)', '', construction, count=1), re.sub(r'\((.+?)\)', r'\1', construction, count=1)])
        if '(' in construction:
            new = []
            for c in constructions[-1]:
                new.extend([re.sub(r'\(.+?\)', '', c, count=1), re.sub(r'\((.+?)\)', r'\1', c, count=1)])
            if new:
                constructions.append(new)
    if '/' in construction:
        new = []
        for c in constructions[-1]:
            flag = []
            optional = re.findall(r'([А-Яа-яЁёA-Za-z\-]+)/([А-Яа-яЁёA-Za-z-]+)/*([А-Яа-яЁёA-Za-z-]+)*', c)
            # print(optional)
            for word in optional[0]:
                # print(word)
                if word:
                    flag.append(re.sub(r'([А-Яа-яЁёA-Za-z\-]+)/([А-Яа-яЁёA-Za-z-]+)/*([А-Яа-яЁёA-Za-z-]+)*', word, c, count=1))
            # print('flaaaaag', flag)
            if len(optional) > 1:
                new_1 = []
                for word in optional[1]:
                    if word:
                        new_1.extend([re.sub(r'([А-Яа-яЁёA-Za-z\-]+)/([А-Яа-яЁёA-Za-z-]+)/*([А-Яа-яЁёA-Za-z-]+)*', word, i, count=1) for i in flag])
                # print('new_1', new_1)
                new.extend(new_1)
            else:
                new.extend(flag)
            # print(new)
    if not new:
        new = [construction]

    constructions.append(new)
    #print(constructions[-1])
    final_list = list(set([i.replace('XP', '').replace('Cop', '').replace('Crd', '').replace('Ord', '').replace('Cl', '')
                          for i in constructions[-1]]))
    return final_list


def make_query(construction):
    construction = nltk.word_tokenize(construction)
    construction = [c.split('-')[0] for c in construction] # Берем только первый элемент от каждого токена конструкции (без учета атрибута)
    search_columns = []  # Определяем колонки, по которым нужно искать
    for i in construction:
        if i in POS_TAGS.values():
            search_columns.append('pos')
        elif i == morph.parse(i)[0].normal_form:
            search_columns.append('lemma')
        else:
            search_columns.append('form')
    return construction, search_columns

def list_of_queries(construction):
    construction = construction.replace('NP', 'Noun').replace('VP', 'Verb')
    list_of_queries = []
    for option in get_all_types(construction):
        if '~' in option:
            continue
        list_of_queries.append(make_query(option))
    if not list_of_queries:
        print('Кажется, я пока не справлюсь с такой конструкцией')
    return list_of_queries


def search(query, cur):
    if not query:
        print('Кажется, я такого не нашел')
    new_id = cur.execute("""SELECT id FROM data""").fetchall()  # Initiating ids of supportive table
    for token, col in zip(query[0], query[1]):
        cur.executemany("""INSERT INTO check_id (id) VALUES (?)""", new_id)
        new_id = cur.execute("""SELECT A.new_id
                                FROM (SELECT id, {0}, 
                                    LEAD(id) OVER(ORDER BY id) new_id
                                FROM data) 
                                 as A 
                                 WHERE A.{0} == '{1}' AND A.id IN check_id;""".format(col, token)).fetchall()
        cur.execute("""DELETE FROM check_id""")

    cur.executemany("""INSERT INTO check_id (id) VALUES (?)""", new_id)

    data = cur.execute("""SELECT sent_id, word FROM data
                          WHERE sent_id IN
                                      (SELECT sent_id FROM data 
                                      WHERE id IN check_id)

                        """).fetchall()
    result = []
    if not data:
        return ''
    sent = data[0][1]
    for i in range(len(data))[1:]:
        if data[i][0] == data[i - 1][0]:
            sent = sent + ' ' + data[i][1]
        else:
            result.append(sent.replace(' ,', ',').replace(' .', '.'))
            sent = data[i][1]
    result.append(sent.replace(' ,', ',').replace(' .', '.'))
    cur.execute("""DELETE FROM check_id""")
    if len(result) > 10:
        result = random.sample(result, 10)

    return result


st.title('Russian Constructicon')
st.sidebar.subheader("About the App")
st.sidebar.text("Russian constructions searching tool")
st.sidebar.info(
    "Use this tool to get the examples of your constructions. The search is based on Taiga corpus. "
    "POS attributes, clausal and reduplication search is yet to be developed. "
    "I am open for your comments and suggestions.")
st.sidebar.subheader("Developed by")
st.sidebar.text("Anna Aksenova (Telegram: @aksenysh_)")

con = sqlite3.connect('constr.db', timeout=10)
with st.form(key='my_form'):
    construction = st.text_input(label='Type construction formula')
    submit_button = st.form_submit_button(label="Search")
if submit_button:
    if construction:
        start = time.time()
        cur = con.cursor()
        examples = {' '.join(query[0]): search(query, cur) for query in list_of_queries(construction)}
        cur.close()
        beautiful_print = []
        for ctype in examples.keys():
            beautiful_print.append('**' + str(ctype) + '**' + '  \n')
            if not examples[ctype]:
                beautiful_print.append("""*Ooops, sorry! Don't know this construction yet:(*""" + '  \n')
            else:
                for ix, ex in enumerate(examples[ctype]):
                    beautiful_print.append(str(ix+1) + '. ' + ex + '  \n')
        beautiful_print = ''.join(beautiful_print)
        end = time.time()
    else:
        start = time.time()
        beautiful_print = '*Ehm, type your query first*'
        end = time.time()
    time_delta = end - start
    st.write("""*Thanks for your patience! It took me {} sec and look what I've found:*""".format(round(time_delta, 3)))
    st.markdown(beautiful_print)
