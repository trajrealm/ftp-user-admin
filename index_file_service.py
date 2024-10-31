

import conf.app_config as app_config


def read_file_with_doc_links(selected_datasets=None, csv_file_path=app_config.DOC_LINKS_CSV_FILEPATH):
    if selected_datasets is  None:
        return
    doclinks = dict()
    with open(csv_file_path, 'r') as fp:
        lines = fp.readlines()
        for line in lines:
            splitted = line.strip().split(",")
            if splitted[0] not in selected_datasets:
                continue
            if splitted[0] != '':
                if splitted[0] not in doclinks:
                    doclinks[splitted[0]] = dict()
                if splitted[1] not in doclinks[splitted[0]]:
                    doclinks[splitted[0]][splitted[1]] = splitted[2]
    return doclinks


def read_file_with_data_links(csv_file_path=app_config.DATA_LINKS_CSV_FILEPATH):
    datalinks = dict()
    with open(csv_file_path, 'r') as fp:
        lines = fp.readlines()
        for line in lines:
            splitted = line.strip().split(",")
            if splitted[0] != '':
                if splitted[0] not in datalinks:
                    datalinks[splitted[0]] = (splitted[1], splitted[2])
    return datalinks


def add_datalinks(doc_links_dict, data_links_csv=app_config.DATA_LINKS_CSV_FILEPATH):
    datalinkmap = read_file_with_data_links(data_links_csv)
    for d in doc_links_dict:
        doc_links_dict[d][datalinkmap[d][0]] = datalinkmap[d][0]
    return doc_links_dict


def create_index_file(html_string):
    with open('tmp/index.html' , 'w') as f:
        f.write(html_string)


def generate_html_string(doclinks_dict, update_prepend_string=None, html_title=app_config.HTML_INDEX_TITLE, html_header=app_config.HTML_INDEX_HEADER):
    html_string = """
    <html>
        <head>
            <title>%s</title>
        </head>
        <body>
            <h2>%s</h2>
            <ul style="list-style-type:none; padding-left: 10px"> 
    """ % (html_title, html_header)
    if update_prepend_string is not None:
        html_string += update_prepend_string

    written = set()
    for d in doclinks_dict:
        for x in doclinks_dict[d]:
            if x not in written:
                html_string += "<li><a href='%s'>%s</a></li>" % (doclinks_dict[d][x], x) + "\n"
                written.add(x)

    html_string += """
    </ul>
    </body>
    </html>
    """
    return html_string


def read_lines_from_index_file_as_string():
    li_string = str()
    with open('tmp/index.html') as f:
        lines = f.readlines()
        for l in lines:
            if "<li>" in l.strip():
                li_string += l.strip() + "\n"
    return li_string


def indexfile_create(selected_datasets):
    doclinks_dict = read_file_with_doc_links(selected_datasets=selected_datasets)
    doc_and_data_links = add_datalinks(doclinks_dict)
    html_string = generate_html_string(doc_and_data_links)
    create_index_file(html_string)


def indexfile_update(selected_datasets):
    doclinks_dict = read_file_with_doc_links(selected_datasets=selected_datasets)
    doc_and_data_links = add_datalinks(doclinks_dict)
    existing_lines = read_lines_from_index_file_as_string()
    html_string = generate_html_string(doc_and_data_links, update_prepend_string=existing_lines)
    create_index_file(html_string)