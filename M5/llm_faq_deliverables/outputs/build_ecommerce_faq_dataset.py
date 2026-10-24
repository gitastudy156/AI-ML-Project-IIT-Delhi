"""Synthetic e-commerce (fictional store "ShopEase") customer-support FAQ generator.

Usage:  python build_ecommerce_faq_dataset.py [out.jsonl] [seed]

Output: JSONL, one object per line:
        {"prompt": "...", "response": "...", "qid": "<question-group id>"}
"prompt"/"response" follow the assignment format. "qid" marks paraphrases of the same base
question so that the notebook can split train/val/test WITHOUT leaking near-duplicates.
All answers are consistent with one fictional policy sheet (30-day returns, free shipping over $50, ...).
"""
import json
import random
import sys

# ---------------------------------------------------------------------------
# (topic_id, [question paraphrases], [answer variants])  -- all facts are fictional
# ---------------------------------------------------------------------------
TOPICS = [
    ("return_window",
     ["Can I return a product after 30 days?", "What is your return policy?", "How long do I have to return an item?",
      "Is there a time limit for returns?", "I bought something 40 days ago, can I still send it back?",
      "Until when can I return my order?"],
     ["Returns are accepted within 30 days of delivery. After that we cannot take the item back, sorry!",
      "You can return items within 30 days of delivery. Once the 30 days are over, returns are no longer possible."]),
    ("return_condition",
     ["What condition must an item be in to be returned?", "Can I return something I have already used?",
      "Do I need the original packaging to return a product?", "Can I return an item without the tags?",
      "Do you accept opened products for return?", "What are the requirements for a return?"],
     ["Items must be unused, in their original packaging and with all tags attached to be eligible for a return.",
      "To be returned, an item has to be unused and in its original packaging with the tags still on."]),
    ("return_how",
     ["How do I return an item?", "How can I start a return?", "What is the process to send something back?",
      "Where do I request a return?", "I want to return my order, what do I do?", "How do I get a return label?"],
     ["Go to My Orders, select the item and click Return Item. You will get a return label by email within a few minutes.",
      "Start the return in My Orders by choosing Return Item. We then email you a printable return label."]),
    ("refund_time",
     ["How long does a refund take?", "When will I get my money back?", "How many days until my refund arrives?",
      "I returned my item, when do I get the refund?", "How fast are refunds processed?",
      "Where does my refund go?"],
     ["Refunds are issued to your original payment method within 5-7 business days after we receive the returned item.",
      "Once we receive your return, the refund goes back to your original payment method in 5-7 business days."]),
    ("return_shipping_cost",
     ["Who pays for return shipping?", "Is return shipping free?", "How much does it cost to send an item back?",
      "Do I have to pay to return a product?", "Are there any return fees?", "What is the return label fee?"],
     ["Return shipping costs $5.99, deducted from your refund. It is free if the item is defective, damaged or the wrong one.",
      "A $5.99 return shipping fee is deducted from your refund, unless the item arrived defective, damaged or incorrect, then it is free."]),
    ("exchange",
     ["Can I exchange an item for a different size?", "Do you offer exchanges?", "I ordered the wrong colour, can I swap it?",
      "How do I exchange a product?", "Is there a fee for exchanges?", "Can I get a different size instead of a refund?"],
     ["Yes, size and colour exchanges are free within 30 days of delivery. Start one from My Orders by choosing Exchange Item.",
      "We offer free size and colour exchanges within 30 days of delivery. Choose Exchange Item in My Orders to begin."]),
    ("final_sale",
     ["Which items cannot be returned?", "Are sale items returnable?", "Can I return a gift card?",
      "Can personalised products be returned?", "What does Final Sale mean?", "Are there any non-returnable products?"],
     ["Items marked Final Sale, gift cards and personalised products cannot be returned or exchanged.",
      "Final Sale items, gift cards and personalised products are not eligible for return or exchange."]),
    ("damaged_item",
     ["My item arrived damaged, what should I do?", "I received a broken product.", "The package was damaged when it arrived, can you help?",
      "What if my order is defective?", "How do I report a damaged item?", "My product does not work, what now?"],
     ["We are sorry about that! Report it within 48 hours of delivery with a photo through My Orders and we will send a free replacement or a refund.",
      "Please report damaged or defective items within 48 hours of delivery and attach a photo in My Orders. We will replace it or refund you for free."]),
    ("wrong_item",
     ["I received the wrong item, what do I do?", "You sent me the wrong product.", "The item in my package is not what I ordered.",
      "How do I report an incorrect item?", "I got someone else's order, help!", "My order has the wrong size, can you fix it?"],
     ["Sorry for the mix-up! Contact support with your order number and a photo and we will ship the correct item free of charge with a prepaid return label.",
      "Please send us your order number and a photo. We will ship the correct item at no cost and include a prepaid label for the wrong one."]),
    ("missing_package",
     ["My tracking says delivered but I did not get my package.", "Where is my package? It says delivered.", "I never received my order.",
      "My parcel is marked as delivered but it is not here.", "What do I do if my package is lost?", "The courier says delivered, but I see nothing."],
     ["Please wait 24 hours and check with neighbours, as carriers sometimes mark parcels early. If it still has not arrived, contact support within 7 days and we will investigate.",
      "Give it 24 hours and ask your neighbours first. If the package is still missing, contact support within 7 days so we can open an investigation."]),
    ("track_order",
     ["How do I track my order?", "Where can I see my order status?", "Where is my order?", "How can I check where my package is?",
      "Can I get a tracking number?", "I want to follow my delivery."],
     ["You can track your order under My Orders by clicking Track. We also email you a tracking link as soon as it ships.",
      "Open My Orders and click Track next to your order. A tracking link is also sent to you by email once the order ships."]),
    ("processing_time",
     ["How long does it take to process my order?", "When will my order ship?", "How soon do you dispatch orders?",
      "My order still says processing, is that normal?", "How many days until my order is shipped?", "What does processing mean?"],
     ["Orders are processed within 1 business day. Once shipped, you receive a confirmation email with tracking details.",
      "We process orders in 1 business day and then email you a shipping confirmation with tracking information."]),
    ("cancel_order",
     ["How do I cancel my order?", "Can I cancel an order I just placed?", "I want to cancel my purchase.",
      "Is it possible to cancel after ordering?", "What if my order already shipped and I want to cancel?", "Where is the cancel button?"],
     ["You can cancel for free from My Orders until the order has shipped. If it has already shipped, refuse the delivery or return it within 30 days.",
      "Open My Orders and click Cancel as long as the order has not shipped. Shipped orders can be returned within 30 days instead."]),
    ("change_address",
     ["Can I change my delivery address?", "I entered the wrong shipping address, what can I do?", "How do I update the address on my order?",
      "Can I change my address after placing the order?", "Can you ship my order to a different address?", "I moved, can I edit the delivery address?"],
     ["You can edit the address in My Orders before the order ships. Once it has shipped, the address can no longer be changed.",
      "The delivery address can be changed in My Orders until the order ships. After shipping it is not possible to change it."]),
    ("modify_order",
     ["Can I add an item to my order?", "Can I change the items in my order?", "I forgot something, can I add it to my existing order?",
      "How do I change the quantity after ordering?", "Can I edit my order after checkout?", "Can I remove an item from my order?"],
     ["Orders cannot be edited after checkout. Please cancel the order in My Orders before it ships and place a new one.",
      "Once placed, an order cannot be modified. Cancel it from My Orders before it ships and reorder with the right items."]),
    ("standard_shipping",
     ["How long does standard shipping take?", "What are your delivery times?", "How much is standard delivery?",
      "How many days will my order take to arrive?", "What does regular shipping cost?", "When will I receive my package?"],
     ["Standard shipping takes 3-5 business days and costs $4.99.",
      "Standard delivery costs $4.99 and arrives within 3-5 business days."]),
    ("free_shipping",
     ["Is there free delivery?", "Do you offer free shipping?", "What is the minimum order for free shipping?",
      "How much do I need to spend to get free shipping?", "Is shipping free on all orders?", "Do orders over $50 ship free?"],
     ["Yes! Standard shipping is free on orders over $50.",
      "Standard shipping is free for orders above $50. Smaller orders pay $4.99."]),
    ("express_shipping",
     ["Do you have express shipping?", "How fast is express delivery?", "How much does express shipping cost?",
      "I need my order quickly, what are my options?", "Can I get next-day delivery?", "What is the cutoff time for express orders?"],
     ["Express shipping costs $12.99 and delivers in 1-2 business days. Order before 2 pm ET to ship the same day.",
      "Yes, express shipping is $12.99 with delivery in 1-2 business days. Orders placed before 2 pm ET ship the same day."]),
    ("international",
     ["Do you ship internationally?", "Do you ship to Canada?", "Can I order from outside the US?",
      "How long does international shipping take?", "Do I pay customs duties on international orders?", "Which countries do you deliver to?"],
     ["We ship to over 40 countries. International delivery takes 7-14 business days and any customs duties or import taxes are paid by the customer.",
      "Yes, we deliver to 40+ countries in 7-14 business days. Customs duties and import taxes are the customer's responsibility."]),
    ("po_box",
     ["Can you ship to a PO box?", "Do you deliver to post office boxes?", "Is express shipping available for P.O. boxes?",
      "Can I use a PO box as a delivery address?", "Do you deliver to parcel lockers?", "Can I ship to an APO address?"],
     ["Standard shipping works for PO boxes, but express shipping needs a street address.",
      "Yes, standard orders can go to a PO box. Express orders require a street address."]),
    ("weekend_delivery",
     ["Do you deliver on weekends?", "Is Sunday delivery available?", "Can my order arrive on a Saturday?",
      "Do business days include weekends?", "Do you ship on holidays?", "What days do you deliver?"],
     ["We deliver Monday to Saturday. There is no Sunday or holiday delivery, and business days do not include weekends.",
      "Deliveries happen Monday through Saturday. We do not deliver on Sundays or holidays, and weekends are not counted as business days."]),
    ("payment_methods",
     ["What payment methods do you accept?", "Can I pay with PayPal?", "Do you take American Express?",
      "Is Apple Pay accepted?", "Which cards can I use at checkout?", "Can I pay with a gift card?"],
     ["We accept Visa, MasterCard, American Express, PayPal, Apple Pay and ShopEase gift cards.",
      "You can pay with Visa, MasterCard, American Express, PayPal, Apple Pay or a ShopEase gift card."]),
    ("payment_declined",
     ["Why was my card declined?", "My payment failed, what should I do?", "Checkout will not accept my credit card.",
      "I get a payment error at checkout.", "My card keeps getting rejected.", "What do I do if my payment is declined?"],
     ["Please check your card number, expiry date and billing address. If everything is correct, contact your bank or try another payment method.",
      "Double-check the card details and billing address first. If it still fails, call your bank or use a different payment method."]),
    ("cod",
     ["Do you offer cash on delivery?", "Can I pay when the order arrives?", "Is COD available?",
      "Can I pay by bank transfer?", "Can I pay in instalments?", "Can I pay with cash?"],
     ["Sorry, cash on delivery is not available. Please pay online with a card, PayPal, Apple Pay or a gift card.",
      "We do not offer cash on delivery. You can pay online by card, PayPal, Apple Pay or gift card."]),
    ("promo_code",
     ["How do I use a promo code?", "Where do I enter my discount code?", "Can I use two coupons on one order?",
      "My coupon code is not working.", "Can promo codes be combined?", "How do I apply a voucher?"],
     ["Enter your code in the Promo Code box at checkout and click Apply. Only one code can be used per order and codes cannot be combined.",
      "Type the code into the Promo Code field at checkout. Each order accepts one code, and codes cannot be combined."]),
    ("welcome_discount",
     ["Do you have a discount for new customers?", "Is there a first order discount?", "How do I get 10% off?",
      "What is the welcome code?", "Do you have a newsletter discount?", "Can I get a coupon for signing up?"],
     ["Yes! Subscribe to our newsletter and use the code WELCOME10 for 10% off your first order.",
      "New customers get 10% off their first order with the code WELCOME10 after subscribing to our newsletter."]),
    ("gift_cards",
     ["Do gift cards expire?", "How do I redeem a gift card?", "How can I check my gift card balance?",
      "Can I buy a gift card for a friend?", "Where do I enter my gift card code?", "Is there an expiry date on gift cards?"],
     ["ShopEase gift cards never expire. Enter the code at checkout and check your balance under Account > Gift Cards.",
      "Gift cards do not expire. Redeem them by entering the code at checkout, and view the balance in Account > Gift Cards."]),
    ("price_adjustment",
     ["The price dropped after I bought it, can I get a refund of the difference?", "Do you offer price matching?", "Can I get a price adjustment?",
      "The item I bought is on sale now, what can I do?", "Do you refund price drops?", "What is your price adjustment policy?"],
     ["If the price drops within 14 days of your purchase, contact support with your order number and we will refund the difference.",
      "We offer price adjustments within 14 days of purchase. Contact support with your order number and we will refund the difference."]),
    ("invoice",
     ["Where can I find my invoice?", "Can I get a receipt for my order?", "How do I download my invoice?",
      "I need an invoice for my company.", "Do you send receipts by email?", "Where is my order receipt?"],
     ["Your invoice is emailed with the order confirmation and can be downloaded anytime from My Orders.",
      "We email the invoice together with your order confirmation. You can also download it from My Orders."]),
    ("sales_tax",
     ["Do you charge sales tax?", "How is tax calculated on my order?", "Why was I charged tax?",
      "Are prices tax inclusive?", "Where can I see the tax amount?", "Is VAT included in the price?"],
     ["Sales tax is calculated at checkout based on your shipping address and shown before you pay.",
      "Tax is added at checkout according to your delivery address, and the exact amount is displayed before you place the order."]),
    ("reset_password",
     ["I forgot my password, help!", "How do I reset my password?", "I cannot log in to my account.",
      "How can I change my password?", "I did not receive the password reset email.", "Where is the forgot password link?"],
     ["Click Forgot Password on the login page and enter your email. We will send a reset link, so please check your spam folder if you do not see it.",
      "Use the Forgot Password link on the login page. A reset link is emailed to you, and it may land in your spam folder."]),
    ("change_email",
     ["How do I change my email address?", "Can I update my account email?", "I want to use a different email for my account.",
      "Where do I edit my profile details?", "How do I change my phone number?", "Can I change my name on my account?"],
     ["Go to Account Settings > Profile to update your email address, phone number or name.",
      "You can edit your email, phone number and name under Account Settings > Profile."]),
    ("delete_account",
     ["How do I delete my account?", "Can I close my account?", "I want my data removed.",
      "How can I deactivate my profile?", "Can you delete my personal information?", "I no longer want an account with you."],
     ["Email support@shopease.example from your registered address to request deletion. Your account and data are removed within 5 business days.",
      "To delete your account, send a request to support@shopease.example from your registered email. It is processed within 5 business days."]),
    ("guest_checkout",
     ["Do I need an account to order?", "Can I check out as a guest?", "Is it necessary to register?",
      "Why should I create an account?", "Can I buy without signing up?", "Do I have to log in to place an order?"],
     ["No, guest checkout is available. An account is optional but lets you track orders, save addresses and earn reward points.",
      "You can check out as a guest. Creating an account is optional, but it lets you track orders and earn rewards."]),
    ("two_factor",
     ["How do I enable two-factor authentication?", "Can I make my account more secure?", "Do you support 2FA?",
      "Where are the security settings?", "How do I turn on login verification?", "Is my account protected with a second step?"],
     ["Yes, turn on two-factor authentication in Account Settings > Security. You will then confirm each login with a code sent to your phone.",
      "We support two-factor authentication. Enable it in Account Settings > Security and confirm logins with a code sent to your phone."]),
    ("account_locked",
     ["My account is locked, what do I do?", "Why can't I log in after several attempts?", "How long is my account locked?",
      "I entered the wrong password too many times.", "It says my account has been temporarily locked.", "How do I unlock my account?"],
     ["After 5 failed login attempts the account is locked for 30 minutes. Wait, or reset your password with Forgot Password to get back in right away.",
      "Five wrong passwords lock the account for 30 minutes. You can wait or use Forgot Password to reset it immediately."]),
    ("warranty",
     ["Do your products have a warranty?", "How long is the warranty on electronics?", "How do I make a warranty claim?",
      "My headphones stopped working after 6 months, is it covered?", "What does the warranty cover?", "Is there a guarantee on electronics?"],
     ["Electronics come with a 1-year manufacturer warranty. To make a claim, contact support with your order number and a description of the problem.",
      "All electronics are covered by a 1-year manufacturer warranty. Contact support with your order number to start a claim."]),
    ("out_of_stock",
     ["The item is out of stock, when will it be back?", "Can I be notified when a product is available again?", "What does sold out mean?",
      "When will you restock?", "How do I get a restock alert?", "Why is my size unavailable?"],
     ["Click Notify Me on the product page and we will email you when it is back. Restocks usually take 2-3 weeks.",
      "Use the Notify Me button on the product page for a restock email. Items are typically back in 2-3 weeks."]),
    ("preorder",
     ["How do pre-orders work?", "When am I charged for a pre-order?", "Can I pre-order an item?",
      "When will my pre-order ship?", "Can I cancel a pre-order?", "What is a pre-order?"],
     ["Pre-ordered items are charged when they ship, and they ship on the release date shown on the product page. You can cancel any time before shipping.",
      "You are charged only when a pre-order ships on its release date, and you can cancel it at any time before then."]),
    ("authentic",
     ["Are your products authentic?", "Do you sell original brands?", "Can I trust that the items are genuine?",
      "Are your products fake or original?", "Where do you source your products?", "Is this a genuine product?"],
     ["Yes, every product is sourced directly from authorised brands and suppliers, so all items are 100% authentic.",
      "All our products come from authorised brands and suppliers and are guaranteed authentic."]),
    ("size_guide",
     ["How do I find my size?", "Where is the size chart?", "Do your clothes run small?",
      "Is there a size guide?", "Which size should I order?", "How do I measure myself?"],
     ["Every product page has a Size Guide link next to the size selector with measurements. If you are between sizes, we recommend sizing up.",
      "Use the Size Guide link beside the size selector on each product page. If you are between two sizes, size up."]),
    ("rewards",
     ["How do reward points work?", "How many points do I earn per dollar?", "Do reward points expire?",
      "How do I redeem my points?", "What is ShopEase Rewards?", "How much is 100 points worth?"],
     ["With ShopEase Rewards you earn 1 point per $1 spent, and 100 points equal $5 off. Points expire after 12 months of account inactivity.",
      "You earn 1 point for every $1 spent, and every 100 points are worth $5 off at checkout. Points expire after 12 months without activity."]),
    ("contact_support",
     ["How can I contact customer support?", "What is your support email?", "Do you have live chat?",
      "How long until I get a reply from support?", "Where can I talk to a person?", "How do I reach your team?"],
     ["Email support@shopease.example or use live chat daily from 9 am to 9 pm ET. We reply to emails within 24 hours.",
      "Reach us at support@shopease.example or through live chat from 9 am to 9 pm ET every day. Email replies take up to 24 hours."]),
    ("phone_support",
     ["Do you have a phone number?", "Can I call customer service?", "What are your phone support hours?",
      "Is there a hotline?", "I would rather speak to someone by phone.", "What number do I call for help?"],
     ["Yes, call 1-800-555-0199 Monday to Friday, 9 am to 6 pm ET.",
      "You can call us on 1-800-555-0199 from Monday to Friday, between 9 am and 6 pm ET."]),
    ("physical_store",
     ["Do you have a physical store?", "Can I pick up my order in person?", "Where are your shops located?",
      "Can I visit your showroom?", "Is there a store near me?", "Do you offer in-store pickup?"],
     ["ShopEase is an online-only store, so we have no physical shops or in-store pickup. Everything is delivered to your door.",
      "We are online only. There are no physical stores or pickup points, and every order is delivered to your address."]),
    ("bulk_orders",
     ["Do you offer bulk discounts?", "I want to order in large quantities.", "Can businesses buy in bulk?",
      "Is there a wholesale price?", "I need 50 units, can I get a deal?", "Do you offer corporate orders?"],
     ["For orders of 10 or more items, email bulk@shopease.example and our team will send you a custom quote.",
      "Bulk and corporate orders of 10+ items get special pricing. Write to bulk@shopease.example for a quote."]),
    ("gift_wrap",
     ["Do you offer gift wrapping?", "Can I add a gift message?", "How much is gift wrap?",
      "Can you send my order as a gift?", "How do I add a card to my gift?", "Can I hide the price on a gift order?"],
     ["Yes, gift wrap costs $3.99 per item. Select it at checkout, where you can also add a message card and the invoice will not show prices.",
      "Gift wrapping is $3.99 per item. Choose it at checkout to add a personal message, and prices are left off the packing slip."]),
    ("privacy",
     ["Is my personal data safe?", "Do you sell my information?", "How do you protect my payment details?",
      "What do you do with my data?", "Is it safe to enter my card on your site?", "Do you share my details with third parties?"],
     ["We never sell your personal information, and all payments are encrypted. You can read the full details in our Privacy Policy.",
      "Your data is not sold to anyone, and payments are protected with encryption. See our Privacy Policy for the details."]),
    ("unsubscribe",
     ["How do I unsubscribe from your emails?", "I want to stop receiving promotional emails.", "Can I opt out of the newsletter?",
      "Too many emails, how do I turn them off?", "Where are the email preferences?", "How can I stop marketing messages?"],
     ["Click the Unsubscribe link at the bottom of any email, or change your choices in Account Settings > Email Preferences.",
      "Use the Unsubscribe link in any of our emails or update Account Settings > Email Preferences."]),
    ("reviews",
     ["How do I write a product review?", "Can I leave a review?", "Where can I rate my purchase?",
      "Why can't I review this item?", "Can I edit my review?", "Are the reviews real?"],
     ["After delivery, open My Orders and click Write a Review. Only verified buyers can review, and you can edit your review at any time.",
      "You can review an item from My Orders once it is delivered. Reviews come from verified buyers and can be edited later."]),
    ("no_confirmation_email",
     ["I did not receive an order confirmation email.", "Where is my confirmation email?", "Can you resend my order confirmation?",
      "I placed an order but got no email.", "My order email never arrived.", "How do I know my order went through?"],
     ["Check your spam folder first. You can also see the order in My Orders and resend the confirmation from there, or contact support if it is missing.",
      "Look in your spam folder, then check My Orders where you can resend the confirmation. If the order is not listed, contact support."]),
    ("split_shipments",
     ["Why did my order arrive in two packages?", "Will my items ship together?", "I only received part of my order.",
      "Why do I have two tracking numbers?", "Can you ship everything in one box?", "Part of my order is missing."],
     ["Orders can ship in separate packages from different warehouses, and each package has its own tracking number. You are not charged extra shipping for it.",
      "Items may ship separately from different warehouses, each with its own tracking number, at no extra shipping cost."]),
    ("delivery_delay",
     ["My order is late, what should I do?", "Why is my delivery delayed?", "My package has not moved for days.",
      "It has been 10 days and my order has not arrived.", "Can you check on my late delivery?", "My tracking has not updated."],
     ["Sorry about the delay! If your order is more than 7 days late, contact support with your order number and we will investigate with the carrier.",
      "We apologise for the delay. If it is over 7 days late, send support your order number and we will look into it with the carrier."]),
    ("mobile_app",
     ["Do you have a mobile app?", "Is there a ShopEase app for iPhone?", "Can I shop on my phone?",
      "Where can I download the app?", "Is the Android app available?", "Do I need a separate account for the app?"],
     ["Yes, the ShopEase app is available for iOS and Android. It uses the same account as the website.",
      "You can download the ShopEase app on iOS and Android and sign in with your usual account."]),
    ("out_of_scope",
     ["What is the weather today?", "Can you tell me a joke?", "What is the capital of France?",
      "Who won the football match yesterday?", "Can you give me medical advice?", "Write me a poem about the sea."],
     ["Sorry, I can only help with ShopEase orders, shipping, returns, payments and accounts. For anything else please contact support@shopease.example.",
      "I am the ShopEase support assistant, so I can only answer questions about orders, shipping, returns, payments and accounts."]),
    ("human_agent",
     ["Can I speak to a human?", "I want to talk to an agent.", "This is not helpful, connect me to support.",
      "How do I escalate my complaint?", "I want to file a complaint.", "Can a manager call me back?"],
     ["Of course. Start a live chat from 9 am to 9 pm ET or email support@shopease.example and a team member will take over.",
      "Sure, you can reach a human agent through live chat (9 am to 9 pm ET) or by emailing support@shopease.example."]),
]

PREFIXES = ["Hi, ", "Hello, ", "Hey, ", "Quick question: ", "Excuse me, ", "Hi there! ", "Good morning, "]
SUFFIXES = [" Thanks!", " Please help.", " Thank you.", " Any info would be appreciated.", " Thanks in advance."]


def decap(q):
    """Lower-case the first letter unless it is a pronoun 'I' or the store name."""
    if q.startswith(("I ", "I'", "ShopEase")):
        return q
    return q[0].lower() + q[1:]


def make_variants(q, rng):
    variants = [q]
    kinds = rng.sample(["prefix", "suffix", "both", "lower"], 1 + int(rng.random() < 0.5))
    for k in kinds:
        if k == "prefix":
            variants.append(rng.choice(PREFIXES) + decap(q))
        elif k == "suffix":
            variants.append(q + rng.choice(SUFFIXES))
        elif k == "both":
            variants.append(rng.choice(PREFIXES) + decap(q) + rng.choice(SUFFIXES))
        else:
            variants.append(q.lower().rstrip("?!. "))
    return variants


def build(seed=42):
    rng = random.Random(seed)
    rows, seen = [], set()
    for topic, questions, answers in TOPICS:
        for k, q in enumerate(questions):
            answer = rng.choice(answers)            # same answer for all paraphrases of one base question
            for v in make_variants(q, rng):
                key = v.lower()
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"prompt": v, "response": answer, "qid": f"{topic}_{k}"})
    rng.shuffle(rows)
    return rows


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "ecommerce_faqs.jsonl"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    data = build(seed)
    with open(out, "w", encoding="utf-8") as f:
        for r in data:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(data)} Q&A pairs ({len(TOPICS)} topics, {len({r['qid'] for r in data})} base questions) to {out}")
