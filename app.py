import os
import shutil

import click
from jina.flow import Flow

def clean_workdir():
    if os.path.exists(os.environ['JINA_WORKSPACE']):
        shutil.rmtree(os.environ['JINA_WORKSPACE'])

def config():
    os.environ['JINA_DATA_FILE'] = 'data/icd10.csv'
    os.environ['JINA_WORKSPACE'] = 'workspace'
    os.environ['JINA_PORT'] = str(45678)


def print_topk(resp, sentence):
    for d in resp.search.docs:
        print(f'Ta-Dah🔮, here are what we found for: {sentence}')
        for idx, match in enumerate(d.matches):
            score = match.score.value
            if score < 0.0:
                continue
            code = match.meta_info.decode()
            name = match.text.strip()
            print(f'> {idx:>2d}({score:.2f}) | {code.upper().ljust(6)} | {name}')


def index(num_docs):
    f = Flow().load_config('flow-index.yml')

    with f:
        f.index_lines(
            filepath=os.environ['JINA_DATA_FILE'],
            batch_size=8,
            size=num_docs,
        )


def query(top_k):
    f = Flow().load_config('flow-query.yml')
    with f:
        while True:
            text = input('please type a sentence: ')
            if not text:
                break

            def ppr(x):
                print_topk(x, text)
            f.search_lines(lines=[text, ], output_fn=ppr, top_k=top_k)


def query_restful():
    f = Flow().load_config('flow-query.yml')
    f.use_rest_gateway()
    with f:
        f.block()


def dryrun():
    f = Flow().load_config('flow-index.yml')
    with f:
        f.dry_run()


@click.command()
@click.option(
    '--task',
    '-t',
    type=click.Choice(
        ['index', 'query', 'query_restful', 'dryrun'], case_sensitive=False
    ),
)
@click.option('--num_docs', '-n', default=70000)
@click.option('--top_k', '-k', default=5)
def main(task, num_docs, top_k):
    config()
    workspace = os.environ['JINA_WORKSPACE']
    if task == 'index':
        clean_workdir()
        index(num_docs)
    if task == 'query':
        if not os.path.exists(workspace):
            print(f'The directory {workspace} does not exist. Please index first via `python app.py -t index`')
        query(top_k)
    if task == 'query_restful':
        if not os.path.exists(workspace):
            print(f'The directory {workspace} does not exist. Please index first via `python app.py -t index`')
        query_restful()
    if task == 'dryrun':
        dryrun()


if __name__ == '__main__':
    main()
