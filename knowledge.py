"""
CSC-128 Capstone: the GYMARC knowledge base
Archit Dubey

One self contained fact per document, written in the words a member would use
when asking about it. This file imports nothing, so data flows one way.
"""

DOCUMENTS = [
    {
        "id": "hours",
        "source": "GYMARC front desk hours sheet",
        "text": (
            "GYMARC is open Monday through Friday from 5:00 AM to 11:00 PM, and on "
            "Saturday and Sunday from 7:00 AM to 8:00 PM. The gym opens early on "
            "weekdays and closes earlier on weekends. Holiday hours are different and "
            "are posted at the front desk."
        ),
    },
    {
        "id": "membership_price",
        "source": "GYMARC membership pricing sheet",
        "text": (
            "A GYMARC membership costs 35 dollars per month. That price covers full "
            "access to the gym floor and all equipment. Students get a discount and "
            "pay 25 dollars a month with a valid student ID. There is no contract and "
            "no sign up fee, so the monthly price is the whole cost of joining. "
            "Memberships are not expensive compared to most gyms."
        ),
    },
    {
        "id": "cancel",
        "source": "GYMARC membership agreement",
        "text": (
            "To cancel your GYMARC membership, stop by the front desk or email "
            "support@gym.com. You have to give 30 days notice, so you will be billed "
            "one more time after you cancel. You can also quit, end, or stop coming "
            "this same way."
        ),
    },
    {
        "id": "freeze",
        "source": "GYMARC membership agreement",
        "text": (
            "If you need a break from GYMARC without cancelling, you can freeze or "
            "pause your account for up to three months. A frozen account is not billed "
            "while it is paused and keeps your current rate when you come back. Ask at "
            "the front desk to put your plan on hold for a few weeks or months."
        ),
    },
    {
        "id": "classes",
        "source": "GYMARC group class schedule",
        "text": (
            "GYMARC runs group classes every day, including yoga, spin, and Zumba. "
            "Classes are included with any membership at no extra cost. The current "
            "class schedule is posted on the website and at the front desk. You do not "
            "need to sign up ahead of time, but popular classes fill up."
        ),
    },
    {
        "id": "personal_training",
        "source": "GYMARC personal training rates",
        "text": (
            "Personal training at GYMARC costs 50 dollars for a single session, or 180 "
            "dollars for a pack of four sessions. A trainer will build you a workout "
            "plan and coach you through it. Sessions run for one hour and you can book "
            "one through this assistant or at the front desk."
        ),
    },
    {
        "id": "guests",
        "source": "GYMARC guest policy",
        "text": (
            "GYMARC members can bring a friend or guest to work out with them. Your "
            "first guest each month is free, and any guest after that costs 10 dollars "
            "for a day pass. Every guest has to sign a waiver at the front desk before "
            "working out, and guests under 18 need a parent to sign for them."
        ),
    },
    {
        "id": "facilities",
        "source": "GYMARC facility guide",
        "text": (
            "GYMARC has a lap pool, a sauna, and locker rooms with showers. Parking is "
            "free in the lot outside. Bring your own lock for the lockers and your own "
            "towel, because GYMARC does not hand out towels."
        ),
    },
    {
        "id": "equipment",
        "source": "GYMARC facility guide",
        "text": (
            "The GYMARC gym floor has treadmills, bikes, rowing machines, free weights, "
            "squat racks, and cable machines. Machines are first come first served and "
            "cannot be reserved. Wipe down equipment after you use it."
        ),
    },
    {
        "id": "joining",
        "source": "GYMARC membership pricing sheet",
        "text": (
            "To join GYMARC, come to the front desk with a photo ID and sign up in "
            "person. You can start the same day you sign up. Bring proof of enrollment "
            "if you are signing up at the student rate."
        ),
    },
]
