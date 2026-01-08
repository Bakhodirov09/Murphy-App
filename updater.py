from web.database import SessionLocal
from web.models import MurphyExerciseQuestionsModel

def update(questions):
    db = SessionLocal()
    try:
        for question in questions:
            question_db = db.query(MurphyExerciseQuestionsModel).filter(
                exercise_id=question['exercise_id'],
                id=question['id']
            ).first()
            text = ""
            for q in question['field']['question']:
                text += q
            question_db.field = {"question": text, "correct_answers": question['field']['options']}
            db.commit()
    finally:
        db.close()

questions = {
	"questions": [
		{
			"id": "9e4d76f7-de97-4749-ad47-62dba107811a",
			"field": {
				"options": [
					"is singing"
				],
				"question": [
					"<strong>City&nbsp;Hall</strong> <br> Elisa Gonzalez {%answer%} songs from Brazil",
					" Argentina and Mexico on Friday at 7 pm."
				],
				"correct_answers": [
					""
				]
			},
			"created_at": "2026-01-08T18:43:04.630305",
			"exercise_id": "50dce2da-1362-4e65-93d4-68ac902bd26e",
			"updated_at": "2026-01-08T18:43:04.630493"
		},
		{
			"id": "025fb2b8-2350-4af9-b4f1-67cda156ac75",
			"field": {
				"options": [
					"is playing",
					"are playing"
				],
				"question": [
					"<strong>Hampton&nbsp;Sports&nbsp;Stadium</strong> <br> Hampton Juniors football team {%answer%} against a team from Germany at 11 am on Sunday."
				],
				"correct_answers": [
					""
				]
			},
			"created_at": "2026-01-08T18:43:04.630305",
			"exercise_id": "50dce2da-1362-4e65-93d4-68ac902bd26e",
			"updated_at": "2026-01-08T18:43:04.630493"
		},
		{
			"id": "a94992c6-559d-4b3e-b095-f08a72f15416",
			"field": {
				"options": [
					"are holding"
				],
				"question": [
					"<strong>The&nbsp;Pavilion<strong> <br> Local jewellers {%answer%} their Summer Sale this Sunday from 10 am to 2 pm."
				],
				"correct_answers": [
					""
				]
			},
			"created_at": "2026-01-08T18:43:04.630305",
			"exercise_id": "50dce2da-1362-4e65-93d4-68ac902bd26e",
			"updated_at": "2026-01-08T18:43:04.630493"
		},
		{
			"id": "1762a9de-958a-4325-9f8c-7c47358a37e0",
			"field": {
				"options": [
					"are offering"
				],
				"question": [
					"<strong>Shoppers’&nbsp;Paradise</strong> (off Main Street) <br> All shoe shops {%answer%} the chance to buy one pair get one pair free every day this week!"
				],
				"correct_answers": [
					""
				]
			},
			"created_at": "2026-01-08T18:43:04.630305",
			"exercise_id": "50dce2da-1362-4e65-93d4-68ac902bd26e",
			"updated_at": "2026-01-08T18:43:04.630493"
		},
		{
			"id": "13cd554a-06ee-4075-a928-f784dd926103",
			"field": {
				"options": [
					"is organising"
				],
				"question": [
					"<strong>Hampton&nbsp;College&nbsp;of&nbsp;Further&nbsp;Education</strong> <br> The education department {%answer%} an open day on Thursday – discover their range of full- and part-time courses."
				],
				"correct_answers": [
					""
				]
			},
			"created_at": "2026-01-08T18:43:04.630305",
			"exercise_id": "50dce2da-1362-4e65-93d4-68ac902bd26e",
			"updated_at": "2026-01-08T18:43:04.630493"
		}
	]
}

print(update(questions))
