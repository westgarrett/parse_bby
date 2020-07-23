
def main():
    option = ""
    while True:
        option = input("Writing to UNL SKUS (U) or Carrier SKUS (C)? (CTRL + C to exit) \nU/C : ")
        option.strip().lower()
        if option == "u" or option == "c":
            break

    if option == "U".lower():
        file = open("unl_skus.txt", "w")
    else:
        file = open("carrier_skus.txt", "w")

    sku = ""
    print("\n\nEnter 0 to exit writer")
    while sku != -1:
        sku = str(input("\n\nPlease enter the sku followed by a newline character: "))
        sku.strip()
        if len(str(sku)) == 7:
            print(f"Writing {sku} to file.")
            file.write(sku + "\n")
        elif sku != "0":
            print("\nNot a valid SKU. Must be 7 digits long. Try again")
        else:
            break

    print(f"\n\nFinished writing. Closing {file}")


main()