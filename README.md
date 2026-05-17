# FNOL Agent — First Notice of Loss Processor


## Setup (2 steps)
pip install flask
python app.py        # Web UI → http://localhost:5000
# OR
python agent.py      # CLI — processes all sample FNOLs
```

## Project Structure
```
fnol-agent/
├── agent.py              
├── app.py                
├── requirements.txt      
└── sample_fnols/
    ├── fnol_001.txt      
    ├── fnol_002.txt      
    ├── fnol_003.txt      
    ├── fnol_004.txt      
    └── fnol_005.txt      
```

## CLI Usage
bash
python agent.py                               # all samples
python agent.py sample_fnols/fnol_001.txt     # single file
python agent.py /path/to/any_fnol.txt         # your own file
python agent.py --output-dir ./results        # custom output dir
python agent.py --no-save                     # skip JSON files
```

## Output Format (JSON)
json
{
  "extractedFields": {
    "policy_number": "POL-2024-78432",
    "policyholder_name": "Rajesh Kumar",
    "effective_date_start": "01-Jan-2024",
    "effective_date_end": "31-Dec-2024",
    "incident_date": "15-Mar-2024",
    "incident_time": "14:35",
    "incident_location": "MG Road, Bengaluru",
    "incident_description": "Rear-end collision...",
    "claimant_name": "Rajesh Kumar",
    "claimant_contact": "+91-9876543210",
    "asset_type": "Motor Vehicle",
    "asset_id": "KA-01-MH-2345",
    "estimated_damage": "18500",
    "claim_type": "Motor - Accidental Damage",
    "attachments": "Photos, FIR copy",
    "initial_estimate": "18500"
  },
  "missingFields": [],
  "recommendedRoute": "Fast-track",
  "reasoning": "All mandatory fields present and estimated damage (Rs.18,500) is below the Rs.25,000 threshold."
}


