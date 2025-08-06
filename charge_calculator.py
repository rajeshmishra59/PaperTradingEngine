# File: charge_calculator.py
# Simulates brokerage and statutory charges for a trade.

def calculate_charges(quantity: int, price: float, is_intraday: bool = True):
    """
    Calculates estimated charges for a single leg of a trade (either buy or sell).
    This version handles both Intraday and Delivery scenarios accurately.
    """
    turnover = quantity * price
    
    # Ab brokerage aur STT, trade ke type (Intraday/Delivery) par depend karega.
    if is_intraday:
        # Intraday ke liye: Flat Rs. 20 brokerage
        brokerage = 20
        # Intraday STT
        stt = (0.00025 * turnover)
    else:
        # Delivery ke liye: Zero brokerage
        brokerage = 0
        # Delivery STT
        stt = (0.001 * turnover)
    
    # Baaki sabhi charges waise hi rahenge
    txn_charges = 0.0000345 * turnover
    gst = 0.18 * (brokerage + txn_charges)
    sebi_charges = 0.000001 * turnover
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