#!/usr/bin/env python3

def main():
    input_filename = "Top207-probable-v2.txt"
    output_filename = "Top207-probable-v2-filtered.txt"
    
    with open(input_filename, "r", encoding="utf-8") as infile, \
         open(output_filename, "w", encoding="utf-8") as outfile:
        for line in infile:
            # Remove newline characters and surrounding whitespace
            password = line.strip()
            
            # Check minimum length of 8 characters
            if len(password) < 8:
                continue

            # Count the number of letters in the password
            letter_count = sum(1 for char in password if char.isalpha())
            if letter_count < 2:
                continue
            
            # Write the valid password to the output file
            outfile.write(password + "\n")

if __name__ == "__main__":
    main()
