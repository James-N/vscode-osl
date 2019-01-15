import http.client
from io import BufferedWriter, BufferedReader

I_USERAGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
I_HOST = 'raw.githubusercontent.com'
I_TEX_URL = 'https://raw.githubusercontent.com/imageworks/OpenShadingLanguage/master/src/doc/languagespec.tex'

def download_document(outfile):
    headers = {
        'user-agent': I_USERAGENT
    }

    conn = http.client.HTTPSConnection(I_HOST)
    try:
        conn.request('GET', I_TEX_URL, headers=headers)
        rsp = conn.getresponse()

        CHUNK_SIZE = 1024 * 10

        reader = BufferedReader(rsp)
        with open(outfile, 'wb') as outf:
            writer = BufferedWriter(outf)
            while True:
                data = reader.read(CHUNK_SIZE)
                if len(data) > 0:
                    writer.write(data)
                else:
                    break
    finally:
        conn.close()


def main(outfile):
    download_document(outfile)

if __name__ == "__main__":
    main('./spec.tex')