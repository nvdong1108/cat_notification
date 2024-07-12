from datetime import  datetime


if __name__ == "__main__":
   now = datetime.now();
   fm_now = now.strftime("%Y%m%d%H%M%S")+str(now.microsecond)
   print(fm_now)

