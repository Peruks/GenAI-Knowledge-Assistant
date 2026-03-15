from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_document():
    
    with open("data/company_policy.txt", "r", encoding="utf-8") as file:
        text = file.read()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=50
    )

    chunks = splitter.split_text(text)

    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:\n")
        print(chunk)

if __name__ == "__main__":
    load_document()