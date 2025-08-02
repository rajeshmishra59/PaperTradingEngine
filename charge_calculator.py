# File: charge_calculator.py
# Simulates brokerage and statutory charges for a trade.

def calculate_charges(quantity: int, price: float, is_intraday=True):
    """
    Calculates estimated charges for a single leg of a trade (either buy or sell).
    Note: These are approximations based on a typical discount broker in India (e.g., Zerodha).
    
    Returns a dictionary containing a breakdown of charges.
    """
    turnover = quantity * price
    
    # 1. Brokerage (Flat fee per order)
    brokerage = min(20, 0.0003 * turnover) if is_intraday else 0
    
    # 2. STT (Securities Transaction Tax)
    stt = (0.00025 * turnover) if is_intraday else (0.001 * turnover)
    
    # 3. Transaction Charges (Exchange fees)
    txn_charges = 0.0000345 * turnover
    
    # 4. GST (on Brokerage + Transaction Charges)
    gst = 0.18 * (brokerage + txn_charges)
    
    # 5. SEBI Charges
    sebi_charges = 0.000001 * turnover
    
    # 6. Stamp Duty (on buy-side only, but we'll average it for simplicity)
    stamp_duty = 0.00003 * turnover
    
    total_charges = brokerage + stt + txn_charges + gst + sebi_charges + stamp_duty
    
    return {
        "turnover": turnover,
        "brokerage": brokerage,
        "stt": stt,
        "txn_charges": txn_charges,
        "gst": gst,
        "total": total_charges
    }