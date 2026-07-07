# APTime — APU Free Slot Finder

> A web-based timetable comparison tool for APU students. Find common free time slots across multiple intakes instantly.

![APTime](static/logo.png)

---

## What is APTime?

APTime helps APU students find the best time to hang out, eat together, or plan group activities by comparing timetables across different intakes. Enter your intake codes, select a week, filter out elective modules not shared by everyone, and APTime highlights all common free slots on a visual timetable grid.

---

## Features

- Compare timetables across **multiple APU intakes** simultaneously
- Filter by **group number** (G1–G5) for split intakes
- Select **current or upcoming week** to plan ahead
- Ignore **CT elective modules** not shared by everyone
- Visual **timetable grid** with colour-coded free and busy slots
- **Free slot summary** showing exact time ranges per day
- Clean **two-panel dashboard** layout — no page reloading needed
- Powered by **APSpace's live open API** — always up to date

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Frontend | HTML, CSS, JavaScript |
| Data Source | APSpace Open Timetable API |
| Styling | Custom CSS (white theme) |

---

## Prerequisites

Before running APTime, make sure you have the following installed:

- **Python 3.8 or above** — [Download here](https://www.python.org/downloads/)
- **pip** (comes with Python)
- A modern web browser (Chrome, Firefox, Edge)

---

## Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/haoyueliew/APTime.git
cd APTime
```

Or download the ZIP from GitHub and extract it.

---

### Step 2 — Install dependencies

```bash
pip install flask requests
```

---

### Step 3 — Folder structure

Make sure your folder looks like this before running:

```
APTime/
├── app.py
├── static/
│   ├── style.css
│   └── logo.png
└── templates/
    └── index.html
```

---

### Step 4 — Run the app

```bash
python app.py
```

You should see:

```
==================================================
  APU Free Slot Finder - Running!
  Open your browser and go to:
  http://127.0.0.1:5000
==================================================
```

---

### Step 5 — Open in browser

Open your browser and go to:

```
http://127.0.0.1:5000
```

---

## User Manual

### Frame 1 — Input Screen

This is the screen you see when you first open APTime.

#### 1. Add Intake Codes

- Type your intake code in the input box (e.g. `APU2F2511SE`)
- If your intake is split into groups, select the group number (G1–G5) from the dropdown
- Click **+ Add** or press **Enter** to add the intake
- Repeat for each intake you want to compare
- You need **at least 2 intakes** to proceed
- To remove an intake, click the **×** button on its tag

#### 2. Select Week

- Once 2 or more intakes are added, the **Select Week** section appears automatically
- Choose between **This Week** or **Next Week**
- This matches exactly what APSpace shows

#### 3. Set Minimum Free Time

- Use the slider to set the minimum gap needed (15–180 minutes)
- Default is **60 minutes** — recommended for a meal break

#### 4. Find Common Free Slots

- Click **Find Common Free Slots →** to proceed
- APTime will fetch the timetable data and load the dashboard

---

### Frame 2 — Dashboard

After clicking Find, the layout switches to the dashboard.

#### Left Panel

Shows a summary of your search:
- APTime logo and title
- Intake codes entered
- Selected week
- Minimum free time
- **← New Search** button to go back to Frame 1

#### Right Top — Filter Elective Modules

- All CT elective modules found across your intakes are shown as chips
- **Tick** any module to ignore it — useful for electives not everyone takes
- Crossed-out chips turn red to indicate they are excluded
- Click **↻ Recompute** after ticking/unticking to update the results

#### Right Bottom Left — Timetable Grid

- A visual Mon–Fri grid from 8:00 AM to 6:00 PM
- 🟩 **Green** = everyone is free during that slot
- ⬜ **Light grey** = at least one intake has class

#### Right Bottom Right — Free Slots Summary

- Lists exact free time ranges per day
- Shows duration in minutes for each gap
- "Onwards →" indicates no more classes for the rest of the day

---

## How Intake Codes Work

APU intake codes follow this format:

```
APU2F2511SE
│   │ │ │└─ Programme (e.g. SE = Software Engineering)
│   │ │ └── Year (e.g. 25 = 2025)
│   │ └──── Month (e.g. 11 = November)
│   └─────── Level (e.g. 2F = Foundation Year 2)
└─────────── Campus (APU / APD)
```

You can find your intake code in APSpace under the **Timetable** section.

---

## Known Limitations

- APTime only shows weeks that APSpace currently has data for (usually current week + next week)
- Timetable data is fetched live from APSpace — an internet connection is required
- The app runs locally and is not hosted online — you need to run `python app.py` each time
- Online classes scheduled after 5:45 PM may appear but the grid caps at 6:00 PM

---

## Contributing

Pull requests are welcome! If you find a bug or want to suggest a feature, open an issue on GitHub.

---

## Author

**Hao Yue** — APU Year 2 Software Engineering Student

---

## License

This project is for educational purposes. Timetable data is sourced from APSpace's public open API.
