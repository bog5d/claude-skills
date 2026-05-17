#!/usr/bin/env python3
"""English Tutor Engine — SM-2 Spaced Repetition + Word Bank + Quiz System"""
import sqlite3, datetime, random, os, sys

DB = os.path.expanduser("~/.hermes/scripts/english_tutor/vocab.db")

def sm2_update(ease_factor, interval, repetitions, quality):
    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0: interval = 1
        elif repetitions == 1: interval = 6
        else: interval = round(interval * ease_factor)
        repetitions += 1
    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if ease_factor < 1.3: ease_factor = 1.3
    return ease_factor, interval, repetitions

def add_word(word, meaning="", phonetic="", example=""):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO words (word, phonetic, meaning, example) VALUES (?,?,?,?)",
                  (word.strip().lower(), phonetic, meaning, example))
        conn.commit()
        wid = c.lastrowid
        conn.close()
        return True, wid, f"OK {word} added (#{wid})"
    except sqlite3.IntegrityError:
        conn.close()
        return False, None, f"DUP {word} already exists"

def get_stats():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    mastered = c.execute("SELECT COUNT(*) FROM words WHERE status='mastered'").fetchone()[0]
    learning = c.execute("SELECT COUNT(*) FROM words WHERE status='learning'").fetchone()[0]
    review = c.execute("SELECT COUNT(*) FROM words WHERE status='review'").fetchone()[0]
    new = c.execute("SELECT COUNT(*) FROM words WHERE status='new'").fetchone()[0]
    today = c.execute("SELECT COUNT(*) FROM reviews WHERE date(reviewed_at)=date('now')").fetchone()[0]
    due = c.execute("SELECT COUNT(*) FROM words WHERE next_review <= datetime('now') OR next_review IS NULL").fetchone()[0]
    conn.close()
    cov = round(total / 55, 1)
    if total < 500: band, level, advice = "30-40", "基础", "词汇量严重不足，先集中背高频词"
    elif total < 1500: band, level, advice = "40-50", "提升中", "继续扩大词汇量，配合阅读练习"
    elif total < 3000: band, level, advice = "50-60", "及格线", "加强真题训练，补语法弱项"
    elif total < 4500: band, level, advice = "60-70", "良好", "精做真题，提升阅读速度"
    else: band, level, advice = "70-80", "优秀", "冲刺高分，练写作和翻译"
    return {"total":total,"mastered":mastered,"learning":learning,"review":review,"new":new,
            "reviewed_today":today,"due":due,"coverage_pct":cov,
            "band":band,"level":level,"advice":advice}

def get_due_words(limit=10):
    conn = sqlite3.connect(DB)
    words = conn.execute("SELECT id,word,meaning,ease_factor,interval,repetitions FROM words WHERE next_review<=datetime('now') OR next_review IS NULL ORDER BY next_review ASC NULLS FIRST LIMIT ?",(limit,)).fetchall()
    conn.close()
    return words

def submit_review(word_id, quality):
    conn = sqlite3.connect(DB)
    word = conn.execute("SELECT ease_factor,interval,repetitions FROM words WHERE id=?",(word_id,)).fetchone()
    if not word: conn.close(); return False, "Not found"
    ef, interval, reps = word
    new_ef, new_interval, new_reps = sm2_update(ef, interval, reps, quality)
    new_status = 'mastered' if (new_reps >= 5 and quality >= 3) else 'learning'
    next_rev = (datetime.datetime.now() + datetime.timedelta(days=new_interval)).isoformat()
    conn.execute("UPDATE words SET ease_factor=?,interval=?,repetitions=?,status=?,next_review=?,last_reviewed=datetime('now') WHERE id=?",(new_ef,new_interval,new_reps,new_status,next_rev,word_id))
    conn.execute("INSERT INTO reviews (word_id,score) VALUES (?,?)",(word_id,quality))
    conn.commit(); conn.close()
    return True, f"间隔{new_interval}d | {new_status}"

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if cmd == "stats":
        s = get_stats()
        print(f"TOTAL:{s['total']} MASTERED:{s['mastered']} LEARNING:{s['learning']} DUE:{s['due']} TODAY:{s['reviewed_today']} COV:{s['coverage_pct']}% BAND:{s['band']} LEVEL:{s['level']} ADVICE:{s['advice']}")
    elif cmd == "due":
        for w in get_due_words(10): print(f"#{w[0]} {w[1]} | {w[2]}")
    elif cmd == "add":
        ok, wid, msg = add_word(sys.argv[2], sys.argv[3] if len(sys.argv)>3 else "")
        print(msg)
    elif cmd == "quiz":
        words = get_due_words(5)
        if not words: print("ALL_CLEAR No words due!")
        else:
            for i,w in enumerate(words): print(f"Q{i+1} #{w[0]} {w[1]}|{w[2]}")
