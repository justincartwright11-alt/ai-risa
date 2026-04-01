import json

# Queens of the Ring (London) event runner for April 3, 2026

event = {
    "event_name": "Queens of the Ring",
    "date": "2026-04-03",
    "location": "London, UK",
    "bouts": [
        {
            "fighters": ["Caroline Dubois", "Terri Harper"],
            "title": "WBC Interim Lightweight Title"
        },
        {
            "fighters": ["Ellie Scotney", "Mayelli Flores Rosquero"],
            "title": "IBF & WBO Super Bantamweight Titles"
        },
        {
            "fighters": ["Chantelle Cameron", "Michaela Kotaskova"],
            "title": "Welterweight"
        },
        {
            "fighters": ["Irma Garcia", "Emma Dolan"],
            "title": "Super Flyweight"
        }
    ]
}

with open("C:/ai_risa_data/reports/boxing_queens_of_the_ring_london_2026_04_03_summary.json", "w", encoding="utf-8") as f:
    json.dump(event, f, indent=2)

print("Event summary written: C:/ai_risa_data/reports/boxing_queens_of_the_ring_london_2026_04_03_summary.json")
