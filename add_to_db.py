from web.database import SessionLocal
from web.models import EssentialWordsModel, EssentialUnitsModel
import json

last_created_unit = 1

def add_vocabulary():
    global last_created_unit
    db = SessionLocal()
    try:
        with open('essential_3.json', 'r', encoding='utf-8') as reader:
            data = json.loads(reader.read())
            for unit in data:
                unit_db = EssentialUnitsModel(
                    unit_number=last_created_unit,
                    book_id='0d12f3a6-ca9e-48cc-b6f0-2d22d15567d3'
                )
                db.add(unit_db)
                db.commit()
                for word in unit['wordlist'][:10]:
                    word_db = EssentialWordsModel(
                        word=word['en'],
                        meaning=word.get('desc', 'Not found'),
                        translation_uz=word['uz'],
                        translation_ru=word['ru'],
                        unit_id=unit_db.id,
                        book_id='0d12f3a6-ca9e-48cc-b6f0-2d22d15567d3',
                        photo=f'https://www.essentialenglish.review/apps-data/4000-essential-english-words-3/data/unit-{unit["unit"]}/wordlist/{word.get("image", "26435.png")}'
                    )
                    db.add(word_db)
                    db.commit()
                print(f'Unit added: {last_created_unit}')
                last_created_unit += 1

    except Exception as e:
        db.rollback()
        print(e)
    finally:
        db.close()

if __name__ == "__main__":
    add_vocabulary()
