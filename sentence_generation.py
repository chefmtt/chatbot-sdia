import os
import openai
import csv

openai.api_key = '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'
count = 0
while (count < 3):

    response = openai.Completion.create(
        model="text-davinci-002",
        prompt="Generate greeting phrases",
        temperature=0.9,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0.05,
        presence_penalty=0)

    text = response["choices"][0]['text']
    list = text.split(",")
    print(list)
    if len(list) > 3:
        sentence = ",".join(list[0:len(list) - 2])
        list = [sentence, list[len(list) - 2], list[len(list) - 1]]
    with open('greetings.csv', 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(list)
    count += 1
