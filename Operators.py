prodduct_price=5000
delivery_charge=100
total_price=prodduct_price+delivery_charge
print(total_price)

#
a = 10
b = 3
print(a+b)
print(a-b)
print(a*b)
print(a/b)
print(a//b)
print(a%b)
print(a**b) 
#######################
follower = 100
follower += 2
print(follower)


#####
 a = 10
b = 20
print(a==b)
print(a!=b)
print(a>b)
print(a<b)
print(a>=b)
print(a<=b)

### 
saved_passwords = "1234abc"
enter_passwords = "1234abc"
print(saved_passwords == enter_passwords) 

# logcical operators 

balance = 500
pin_correct = True
if balance >=500 and pin_correct:
    print("withdraw allowed")
else:
    print("failed") 

# simple calculator 

num1 = float(input("Enter first number:"))
num2 = float(input("Enter second number:"))
choice = input("Enter your choice(+,-,*,/)")

if choice == "+":
    print(num1 + num2)
elif choice == "-":
    print(num1-num2)
elif choice == "*":
    print(num1*num2)
elif choice == "/":
    print(num1/num2)
else:
    print("invalid choice ") 

product = input("Enter the product price:")
price = int(input("Enter the price"))
quantity = int(input("Enter the Quantity:"))
discount = int(input("Enter th discount amount:"))
total = price*quantity
final_bill = total - discount
print("prosuct:",product)
print("Total Amount:", total)
print("Final Bill:", final_bill) 


# conditions
password =(input("Enter the password:"))

if password == "admin@357":
    print("Welcome")
else:
    print("invalid password")


age = 10123
if age >= 18:
    print("eligible to get dl")
else:
    print("you are not ready for this")

marks = int(input("Enter your  marks:"))
if marks >=90:
    print("10 CGPA")
elif marks >=80:
    print("9 CGPA")
elif marks >=70:
    print("8 CGPA")
elif marks >=40:
    print("5 CGPA")
else:
    print("congragulations!, Your eligible for backlog:") 

# logical  conditions(or operators)
age = 25
salary = 100000
if age > 18 and salary > 25000:
    print("you are ready for this loan:")
else :
    print("you are not ready for this:")

day = "sunday"
if day == "sunday" or day == "saturday":
    print("holiday") 


day = "monday"
if not day == "sunday":
    print("you can go college:")
else:
    print("you can not go college")
####
Login = True
if not Login:
    print("print Login")
else :
    print("you are already login")



# task
def withdraw_money():
    balance = 5000
    pin = input("Enter the pin:")
    if pin == "123":
        amount = int(input("Enter the withdra amount:"))
        if amount<= balance:
            balance = balance-amount
            print("withdrawal successful")
        else:
            print("Check balance")
            print("remaining balance",balance)
    else :
        print("wrong pin")
withdraw_money() 


# loops 
name = "virat kohli"
for ch in name:
    print(ch)

# whle loop 
count = 1
while count <=5 :
    print(count)
    count += 1

password = ""
while password !="1234":
    password = input("enter password:")
    print("login success")

student = ["ram","alex","rana"]
student.append("sam")
student.remove("alex")
print(student)
