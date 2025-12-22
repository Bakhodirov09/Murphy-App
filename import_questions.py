import httpx

link = "http://127.0.0.1:8000/teacher/"
link += "add-book-unit/"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0ZWFjaGVyIjoiU3VwcG9ydCIsInR5cGUiOiJ0ZWFjaGVyIn0.AnCVum_LWXnmEg4lmiyEb0GjETffazxd170J2dwLR-s"

def add_a_book(name):
    with httpx.Client(cookies={'token': token}) as request:
        response = request.post(
            url=link,
            json={'name': name}
        )
        print(response.json())
add_a_book('English Grammar In Use Fifth Edition')
