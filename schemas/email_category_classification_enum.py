from enum import Enum

class HumanMessageCategory(str, Enum):
    GENERAL_INQUIRY = "General Inquiry"
    QUOTE_REQUEST = "Quote Request"
    TRACKING_REQUEST = "Tracking Request"
    COMBINE_REQUEST = "Combine Request"
    SPAM = "Spam"    
    HI_DAMAGE_CLAIMS = "H/I - Damage or claims"
    HI_ACCOUNTS_PAYABLE = "H/I - Accounts Payable"
    HI_ACCOUNTS_RECEIVABLE = "H/I - Accounts Receivable"
    HI_COMERCIAL_INVOICE = "H/I - Commercial Invoice"
    HI_COMPLEX_REQUEST = "H/I - Complex request" 
    HI_SPOT_QUOTE = "H/I - Spot quote"
    HI_MISC = "H/I - Misc"
    HI_VENDOR_COMM = "H/I - Vendor Comm"
    HI_BOOKING = "H/I - Booking"

target_categories = {
    HumanMessageCategory.HI_COMPLEX_REQUEST.value,
    HumanMessageCategory.HI_DAMAGE_CLAIMS.value,
    HumanMessageCategory.HI_ACCOUNTS_PAYABLE.value,
    HumanMessageCategory.HI_ACCOUNTS_RECEIVABLE.value,
    HumanMessageCategory.HI_COMERCIAL_INVOICE.value,
    HumanMessageCategory.HI_COMPLEX_REQUEST.value,
    HumanMessageCategory.HI_SPOT_QUOTE.value,
    HumanMessageCategory.HI_MISC.value,
    HumanMessageCategory.HI_VENDOR_COMM.value,
    HumanMessageCategory.HI_BOOKING.value
}
