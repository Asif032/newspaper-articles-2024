from datetime import datetime

def convert_to_english(bangla_datetime):
  
  # print(bangla_datetime)

  bangla_to_english_digits = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

  bangla_months = {
      'জানুয়ারি': 'January',
      'ফেব্রুয়ারি': 'February',
      'মার্চ': 'March',
      'এপ্রিল': 'April',
      'মে': 'May',
      'জুন': 'June',
      'জুলাই': 'July',
      'আগস্ট': 'August',
      'সেপ্টেম্বর': 'September',
      'অক্টোবর': 'October',
      'নভেম্বর': 'November',
      'ডিসেম্বর': 'December'
  }
  try:
    date_part, time_part = bangla_datetime.split(', ')

    day, bangla_month, year = date_part.split()
    day = day.translate(bangla_to_english_digits)
    year = year.translate(bangla_to_english_digits)
    month = bangla_months[bangla_month]
    
    time_part = time_part.translate(bangla_to_english_digits)

    english_date_str = f"{day} {month} {year}, {time_part}"

    english_datetime = datetime.strptime(english_date_str, "%d %B %Y, %H:%M")
  except ValueError as e:
    print("Error processing datetime.")
    print(bangla_datetime)
    return bangla_datetime
  
  return english_datetime


# bangla_datetime = '০৮ অক্টোবর ২০২৪, ২২:২৬'
# print(convert_to_english(bangla_datetime))