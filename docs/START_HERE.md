# 👋 Start Here!

Welcome to your Home Finance Splitting System!

## What Is This?

A tool to **fairly split household expenses** between partners based on proportional income.

Instead of splitting 50/50, you split based on who earns what:
- If you earn 70% of household income, you pay 70% of shared costs
- If your partner earns 30%, they pay 30%

**Fair and transparent!**

## Quick Start (3 Steps)

### 1️⃣ Create Your Templates
```bash
python main.py --create-templates Michael Jacqui
```
(Replace with your actual names)

This creates two Excel files with simple tables to fill in.

### 2️⃣ Fill In Your Data

**DEFAULT: NET Income Mode** (Simpler - Recommended!)

**Your Sheet (e.g., Michael_April_2024.xlsx):**
- **Income tab**: List your NET salary (take-home pay from payslip)
- **Expenses tab**: List shared costs YOU paid (groceries, bills, etc.)

**Partner's Sheet (e.g., Jacqui_April_2024.xlsx):**
- Same thing - they fill in their NET income and what they paid

**Important:**
- Only list SHARED household costs, not personal expenses!
- Use NET amounts (take-home pay), not GROSS
- Tax refunds? Add as "Other" income type when you receive them

**Optional:** Want to use GROSS mode (with tax calculations)? Add `--use-gross` flag to commands.

### 3️⃣ Run the Calculation
```bash
python main.py --person-sheets Michael_April_2024.xlsx Jacqui_April_2024.xlsx
```

You'll see:
- Who earned what
- Tax calculations
- Who should pay what percentage
- **Settlement amount**: Who transfers to whom!

## Next Month?

Easy! Just run:
```bash
python main.py --next
```

It automatically finds and processes the next month's files!

## Need Help?

📚 **Documentation is in the `docs/` folder:**

- **New to this?** → Read [GETTING_STARTED.md](docs/GETTING_STARTED.md)
- **Quick reference?** → See [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)
- **How does checkpoint work?** → Read [CHECKPOINT_GUIDE.md](docs/CHECKPOINT_GUIDE.md)
- **What's new?** → Check [WHATS_NEW.md](docs/WHATS_NEW.md)

📁 **Examples are in the `examples/` folder**

## Common Questions

### "What files do I need?"
Just two Excel files per month - one for each person.

### "What goes in the Expenses sheet?"
Only SHARED household costs that YOU paid:
- ✅ Groceries, utilities, rent/bond, insurance
- ❌ Your personal car payment, gym membership, etc.

### "Do I enter net or gross salary?"
**NET** (take-home pay from your payslip). This is the default and simplest mode.

**Optional:** Use GROSS mode with `--use-gross` flag if you want tax calculations.

### "How do I see all months together?"
```bash
python main.py --checkpoint-summary
```

Shows cumulative transfers across all months.

### "Can I process old months?"
Yes! Just create the files and process them in order.

### "What if I make a mistake?"
Just process that month again (it will ask if you want to overwrite).

## File Organization

```
home_finances/
├── main.py              ← Run this!
├── START_HERE.md        ← You are here
├── README.md            ← Full overview
│
├── docs/                ← All documentation
├── examples/            ← Example files and templates
├── src/                 ← Source code (don't need to touch)
└── tests/               ← Unit tests
```

## First Time Setup

1. **Install Python** (3.8 or higher)
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Create templates** (step 1 above)
4. **Start using it!**

## Pro Tips

- Keep consistent filename format: `Name_Month_Year.xlsx`
- Each person maintains their own sheet
- Process monthly or batch process multiple months
- View cumulative summary for annual settlements
- Backup `financial_checkpoint.json` - it has your history!

## That's It!

You're ready to go. Start with the quick start above, then explore the docs for advanced features.

**Questions?** Check the docs in `docs/` folder or run:
```bash
python main.py --help
```

Happy splitting! 💰⚖️
