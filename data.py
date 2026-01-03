from web.models import EssentialWordsModel
from web.database import SessionLocal

def capitalize_words():
    db = SessionLocal()
    try:
        words = db.query(EssentialWordsModel).all()
        for word in words:
            word.translation_uz = word.translation_uz.capitalize()
            word.translation_ru = word.translation_ru.capitalize()

        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
    finally:
        print('✅ Done')
        db.close()

capitalize_words()