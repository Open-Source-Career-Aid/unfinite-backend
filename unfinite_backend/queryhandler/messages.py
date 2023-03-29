def definemessages(prompt, summarytype):

    '''
    summartype 0 - default
    Messages: user: You are an expert summarizer.
    user: Please summarize the following texts, which are in the format id: text_content, into a comprehensive answer to the question.
    user: Instructions: 
    1. Please include in-text numbered citations of the form [id] for any relevant sources cited in the answer. 
    2. Don't add references at the end of the answer. 
    3. Structure the answer into multiple paragraphs where necessary.

    summartype 1 - quick
    Messages: user: You are an expert summarizer.
    user: Please summarize the following texts, which are in the format id: text_content, into a comprehensive answer to the question.
    user: Instructions: 
    1. Please include in-text numbered citations of the form [id] for any relevant sources cited in the answer. 
    2. Don't add references at the end of the answer. 
    3. Keep the answer concise and to the point. Limit the answer to 1 paragraph only.

    summartype 2 - detailed
    Messages: user: You are an expert summarizer.
    user: Please summarize the following texts, which are in the format id: text_content, into a comprehensive answer to the question.
    user: Instructions: 
    1. Please include in-text numbered citations of the form [id] for any relevant sources cited in the answer. 
    2. Don't add references at the end of the answer. 
    3. Provide a detailed answer. Include as many paragraphs as necessary. Try to explain the concepts in detail.

    summartype 3 - simplified
    Messages: user: You are an expert summarizer.
    user: Please summarize the following texts, which are in the format id: text_content, into a comprehensive answer to the question.
    user: Instructions: 
    1. Please include in-text numbered citations of the form [id] for any relevant sources cited in the answer. 
    2. Don't add references at the end of the answer. 
    3. Simplify the answer. Use simple language and avoid technical jargon.
    '''

    messagesdict = {0:[{
        "role": "user",
        "content": "You are an expert summarizer."
    },
    {
        "role": "user",
        "content": "Please summarize the following texts, which are in the format id: text_content, into a comprehensive answer to the question."
    },
    {
        "role": "user",
        "content": """Instructions: 
1. Please include in-text numbered citations of the form [id] for any relevant sources cited in the answer. 
2. Don't add references at the end of the answer. 
3. Structure the answer into multiple paragraphs where necessary."""
    },
    {
        "role": "user",
        "content": prompt
    }],
    1:[{
        "role": "user",
        "content": "You are an expert summarizer."
    },
    {
        "role": "user",
        "content": "Please summarize the following texts, which are in the format id: text_content, into a comprehensive answer to the question."
    },
    {
        "role": "user",
        "content": """Instructions: 
1. Please include in-text numbered citations of the form [id] for any relevant sources cited in the answer. 
2. Don't add references at the end of the answer. 
3. Keep the answer concise and to the point. Limit the answer to 1 paragraph only."""
    },
    {
        "role": "user",
        "content": prompt
    }],
    2:[{
        "role": "user",
        "content": "You are an expert summarizer."
    },
    {
        "role": "user",
        "content": "Please summarize the following texts, which are in the format id: text_content, into a comprehensive answer to the question."
    },
    {
        "role": "user",
        "content": """Instructions: 
1. Please include in-text numbered citations of the form [id] for any relevant sources cited in the answer. 
2. Don't add references at the end of the answer. 
3. Provide a detailed answer. Include as many paragraphs as necessary. Try to explain the concepts in detail."""
    },
    {
        "role": "user",
        "content": prompt
    }],
    3:[{
        "role": "user",
        "content": "You are an expert summarizer."
    },
    {
        "role": "user",
        "content": "Please summarize the following texts, which are in the format id: text_content, into a comprehensive answer to the question."
    },
    {
        "role": "user",
        "content": """Instructions: 
1. Please include in-text numbered citations of the form [id] for any relevant sources cited in the answer. 
2. Don't add references at the end of the answer. 
3. Simplify the answer. Use simple language and avoid technical jargon."""
    },
    {
        "role": "user",
        "content": prompt
    }]}

    return messagesdict[summarytype]