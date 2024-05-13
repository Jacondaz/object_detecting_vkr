abc = "https://www.youtube.com/watch?v=IQlIKg14HI4"
abc2 = "https://www.youtube.com/watch?v=JriGY5KSQhc&t=1864s"
pattern = "https://www.youtube.com/embed/"
temp = abc.split('?')[1]
temp = temp.split('&')[0]
temp = temp.split('=')[1]
print(pattern + temp)