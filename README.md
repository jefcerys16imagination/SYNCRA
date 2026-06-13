# SYNCRA

A web-based group project for my Software Engineering course in my Uni, it's not fully completed yet and there are some components missing, but i'll be sure to finish it before the project deadline. 
it uses with **Flask** and **SQLite**. it's designed to help students manage tasks, weekly schedules, and finances. And all of these in one place with individual accounts per user.

---

## Follow these steps if you want your very own

### Have these installed and givin access to your cmd PATH

- Python 3.8 or higher
- pip
- flask 2.3.0

### Installation

**1. Clone the repository**
```bash
git https://github.com/jefcerys16imagination/SYNCRA
cd SYNCRA
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the app**
```bash
python app.py
```

**4. Open in browser**
```
http://localhost:5050
```

The database (`dashboard.db`) is created automatically on first run.

### And you're set. Don't forget to change the admin password though

---

## Features

### Authentication
- User **registration** and **login** with validation
- Passwords hashed with SHA-256
- Session-based login (persists 7 days)
- Change / Update Password

### Interactive Calendar
- Monthly calendar with navigation
- **Colored dots** per task — one dot per task, color matches task type
- **Hollow ring dots** for recurring/weekly schedule tasks
- **Gold border outline** on dates that have recorded expenses
- Click any date to view and manage that day's data

### Task Management
- Tasks are reactive to the selected calendar date
- Title updates dynamically: *"8th of Monday's Task(s)"*
- Progress bar showing completed vs total tasks
- "All done! " celebration banner when all tasks are checked
- Check/uncheck and delete tasks per day

### Task Settings (Modal)
Accessible via the Pengaturan Tugas** button, with two tabs:

**Task Types**
- Create custom task types with a name and color (green, orange, blue, purple, teal)
- Delete task types

**Weekly Schedule (Recurring Tasks)**
- Create recurring tasks tied to a task type
- Select specific days: Sun Mon Tue Wed Thu Fri Sat
- Each day tracks its own **independent** check/skip status
- Pause or reactivate schedules without deleting
- Delete schedules permanently

### Finance Management
- Record expenses per date with a free-text description
- Dates with expenses show a **gold border** on the calendar
- Expense list is reactive to the selected calendar date

**Budget modes:**
- **Per Month** — budget and stats apply to the current calendar month
- **Per Week** — budget and stats apply to the current week (Mon–Sun)

**Finance panel shows:**
- Donut chart with percentage of budget used
- Total budget, amount used, and remaining funds
- Expense breakdown grouped by description, sorted by amount
- All stats update dynamically when navigating to different dates/periods

---

## Database Schema

| Table | Description |
|-------|-------------|
| `users` | User accounts — id, username, password hash, full_name, role |
| `task_types` | Custom task categories per user — name, color |
| `tasks` | Individual tasks per user per date |
| `expenses` | Expense records per user per date — amount, description |
| `budgets` | Budget amount and mode (monthly/weekly) per user |
| `recurring_tasks` | Weekly schedule definitions — task type + active days |
| `recurring_skips` | Per-day check/skip status for recurring tasks |

All tables use `ON DELETE CASCADE` — deleting a user removes all their data.

---

## Tech Stack

![Skills](https://skillicons.dev/icons?i=py,flask,sqlite,html,css,js,git,github,vscode)

---

## Project Structure

```
dashboard-kelompok/
├── app.py                  # Flask backend — routes, DB logic, auth
├── dashboard.db            # SQLite database (auto-generated on first run)
├── requirements.txt        # Python dependencies
├── fix_db.py               # One-time DB migration script (if needed)
├── templates/
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   └── index.html          # Main dashboard (single-page app)
└── README.md
```

---


## Notes

- All user data is **fully isolated** — each user only sees their own tasks, schedules, and finances
- `SECRET_KEY` is randomly generated on each restart unless set via environment variable. For production:
  ```bash
  export SECRET_KEY="your-long-random-string-here"
  ```
- Weekly recurring task status is tracked **per day** — checking Monday does not affect Tuesday or Wednesday of the same week
- The `dashboard.db` file should be added to `.gitignore` to avoid committing user data
