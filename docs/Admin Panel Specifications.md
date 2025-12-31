2025-12-18 / 08:59

Status:

Tags:


# Admin Panel Specifications

- login page using email and password (no sign up)
	- when clicking the login button a post request is set to https://spinta-backend.vercel.app/api/auth/login with a request body of 
		{
		  "email": "john@email.com",
		  "password": "SecurePass123!"
		}
	- the response is
		{
		  "user": {
		    "user_id": "550e8400-e29b-41d4-a716-446655440000",
		    "email": "john@email.com",
		    "user_type": "coach",
		    "full_name": "John Smith"
		  },
		  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
		}
	- the returned token is a jwt token and it is going to be used for all the following requests

- next page is the main page with the following fields:
	- opponent team, opponent logo, match date (no match time), home team lineup, away team lineup, our score, opponent score, match video
	- when the process match button is clicked no request happens and a fake loading screen is shown, there should be a loading_time variable that could be changed to make testing easier
	- the loading screen should be a multi step screen with text like : processing match, extracting key plays, detecting players event etc..

- next page is the analyzed video page. the page should have a video preview panel showing the 1-2 minutes of the analyzed video, under it should be like a table of the json data(don't show raw json try to show something more meaningful)
	- when the save match analysis button is clicked a request should be sent to https://spinta-backend.vercel.app/api/coach/matches with auth as the jwt token of the previous step the request should have the following fields:
	- opponent_name, match_date, our_score, opponent_score as text and event_file as a .json file
![[Screenshot 2025-12-18 at 9.24.09 AM.png]]

- the opponent_name, match_date, our_score, opponent_score we get from the data inputed in the main page and the .json file is a statsbomb file saved locally.