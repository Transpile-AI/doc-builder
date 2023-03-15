import os
import json

this_dir = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(this_dir, "permitted_namespaces.json"), "r") as file:
    PERMITTED_NAMESPACES = json.loads(file.read())


def trim_namespace(full_namespace):
    for namespace_to_check, permitted_namespace in PERMITTED_NAMESPACES.items():
        if namespace_to_check in full_namespace:
            return permitted_namespace
    return full_namespace


def modify_html_file(html_filepath):
    # Read markup generated by sphinx
    with open(html_filepath) as file:
        html_contents = file.read()

    # Add logo to page header
    logo_index = html_contents.find('    <link rel="stylesheet"')
    end_index = html_contents[logo_index:].find(" />")
    html_contents_mod = (
        html_contents[0 : logo_index + end_index + 4]
        + '      <link rel="icon" type="image/png" href="https://github.com/unifyai/unifyai.github.io/blob/master/img/externally_linked/ivy_logo_only.png?raw=true">\n'
        + html_contents[logo_index + end_index + 4 :]
    )
    html_contents = html_contents_mod

    # Making logo layout responsive
    support_index = html_contents.find(
        '<div class="line"><strong>Supported Frameworks:</strong></div>'
    )
    if support_index != -1:
        p_index = html_contents[support_index:].find("<p") + support_index + 2
        html_contents = (
            html_contents[0:p_index]
            + " class=supported_frameworks"
            + html_contents[p_index:]
        )
        p_end_index = html_contents[support_index:].find("</p>") + support_index
        a_indices = [
            ind + 18
            for ind in range(p_index, p_end_index)
            if html_contents[ind : ind + 18] == "reference external"
        ]
        res = 0
        for a_index in a_indices:
            a_index += res
            html_contents = html_contents[0:a_index] + " logo" + html_contents[a_index:]
            res += 5

    # Replace 3.14 with pi
    html_contents = html_contents.replace("3.141592653589793", "π")

    # Remove # noqa from all files
    # This gets added to the markup in cases of hyperlinks where the line size gets too long
    html_contents = html_contents.replace("# noqa", "")

    # Fix navbar <no title> issue
    replace_dict = {
        "ivy.html": "Functions",
    }
    no_title_exist = html_contents.find("<no title>")
    while no_title_exist != -1:
        for to_replace in replace_dict:
            html_contents = html_contents.replace("<no title>", replace_dict[to_replace], 1)
        no_title_exist = html_contents.find("<no title>")

    meta_index = html_contents.find("<title>&lt;no title&gt; &#8212;")
    if meta_index != -1:
        file_to_check = html_filepath.split("/")[-1]
        if file_to_check in replace_dict:
            html_contents = html_contents.replace("<title>&lt;no title&gt; &#8212;", "<title>{} &#8212;".format(replace_dict[file_to_check]))

    functions_index = html_contents.find("functional/ivy.html")
    if functions_index != -1:
        html_contents = html_contents.replace("functional/ivy.html", "functional/ivy/activations.html")

    functions_index = html_contents.find("../ivy.html")
    if functions_index != -1:
        html_contents = html_contents.replace("../ivy.html", "../../functional/ivy/activations.html")

    # Read all ivy modules for which markup is generated
    with open(os.path.join(this_dir, "ivy_modules.txt"), "r") as f:
        module_names = [line.replace("\n", "") for line in f.readlines()]

    # For every module, update path of its reference in current file
    for module_name in module_names:
        html_contents = html_contents.replace(
            "docs/{}.html".format(module_name),
            '../{}"'.format(module_name.split("_")[-1]),
        )

    # Update namespaces for inline code in documentation
    contents_split1 = html_contents.split('<span class="sig-prename descclassname">')
    contents_split2 = [item.split("</span>") for item in contents_split1]
    contents_split2_modded = [contents_split2[0]] + [
        [trim_namespace(item[0])] + item[1:] for item in contents_split2[1:]
    ]
    contents_split1_modded = ["</span>".join(item) for item in contents_split2_modded]
    html_contents_modded = '<span class="sig-prename descclassname">'.join(
        contents_split1_modded
    )

    # Update links to remove "<no title>" from submodules to be stepped
    breadcrumbs_index = html_contents_modded.find("wy-breadcrumbs")
    no_title_index = html_contents_modded[breadcrumbs_index:].find("&lt;no title&gt;")
    if no_title_index != -1:
        start_index = html_contents_modded[
            0 : breadcrumbs_index + no_title_index
        ].rfind("<li>")
        end_index = html_contents_modded[start_index:].find("</li>")
        html_contents_modded = html_contents_modded.replace(
            html_contents_modded[start_index : start_index + end_index + 6], ""
        )
        no_title_index = html_contents_modded[breadcrumbs_index:].find(
            "&lt;no title&gt;"
        )

    if "functional/ivy/" in html_filepath:
        function_def_index = [
            i
            for i in range(len(html_contents_modded))
            if html_contents_modded.startswith('<dt class="sig sig-object py"', i)
        ]
        function_defs = []
        for index in function_def_index:
            function_def = html_contents_modded[
                index : index + html_contents_modded[index:].find("\n")
            ]
            if "array_methods" in function_def or "container_methods" in function_def:
                function_defs.append(
                    (
                        function_def,
                        index,
                        index + html_contents_modded[index:].find("\n"),
                    )
                )

        submodule_str = "functional/ivy/"
        submodule_start = html_filepath.find(submodule_str) + len(submodule_str)
        submodule_end = submodule_start + html_filepath[submodule_start:].find("/")
        submodule_name = html_filepath[submodule_start:submodule_end]
        res = 0
        for i in range(len(function_defs)):
            function_def, start_index, end_index = (
                function_defs[i][0],
                function_defs[i][1],
                function_defs[i][2],
            )
            path_start = function_def.find('id="') + 4
            path_end = path_start + function_def[path_start:].find('"')
            path = function_def[path_start:path_end]
            if "array_methods" in function_def:
                extension = "array/{}.html#ArrayWith{}.{}".format(
                    submodule_name, submodule_name.capitalize(), path.split(".")[-1]
                )
            else:
                extension = "container/{}.html#ContainerWith{}.{}".format(
                    submodule_name, submodule_name.capitalize(), path.split(".")[-1]
                )
            ref_string = '<a class="reference internal" href="'
            ref_start_index = (
                start_index
                + res
                + html_contents_modded[start_index + res :].find(ref_string)
                + len(ref_string)
            )
            ref_end_index = ref_start_index + html_contents_modded[
                ref_start_index:
            ].find('"><span')
            ref = html_contents_modded[ref_start_index:ref_end_index]
            ref_len = len(ref)
            new_ref_str = "_modules/ivy/"
            new_ref = ref[0 : ref.find(new_ref_str) + len(new_ref_str)]
            new_ref += extension
            new_ref_len = len(new_ref)
            html_contents_modded = (
                html_contents_modded[:ref_start_index]
                + new_ref
                + html_contents_modded[ref_end_index:]
            )
            res += new_ref_len - ref_len

        for i in range(len(function_defs)):
            function_def, start_index, end_index = (
                function_defs[i][0],
                function_defs[i][1],
                function_defs[i][2],
            )
            function_end_index = start_index + html_contents_modded[start_index:].find(
                "</dl>"
            )
            docstring_start_index = (
                start_index + html_contents_modded[start_index:].find("<p>") + 3
            )
            docstring_end_index = docstring_start_index + html_contents_modded[
                docstring_start_index:function_end_index
            ].find("</p>")
            docstring_content = html_contents_modded[
                docstring_start_index:docstring_end_index
            ]
            if (
                docstring_end_index - docstring_start_index < 10
                or docstring_start_index == 3
                or "functional" not in html_filepath
                or "code" in docstring_content
            ):
                continue
            docstring_content = docstring_content.replace("<cite>", "")
            docstring_content = docstring_content.replace("</cite>", "")
            function_call_indices = []
            for i in range(len(docstring_content)):
                if docstring_content.startswith("of ivy.", i):
                    indexes = [
                        index
                        for index in range(i + 7, len(docstring_content))
                        if docstring_content[index] in [" ", "."]
                    ]
                    if len(indexes) == 0:
                        continue
                    index_end = indexes[0]
                    function_call_indices.append((i, index_end))
                if docstring_content.startswith("for ivy.", i):
                    indexes = [
                        index
                        for index in range(i + 8, len(docstring_content))
                        if docstring_content[index] in [" ", "."]
                    ]
                    if len(indexes) == 0:
                        continue
                    index_end = indexes[0]
                    function_call_indices.append((i, index_end))
            function_calls = []
            for index_start, index_end in function_call_indices:
                if docstring_content[index_start] == "f":
                    function_calls.append(
                        (docstring_content[index_start:index_end], False)
                    )
                else:
                    function_calls.append(
                        (docstring_content[index_start:index_end], True)
                    )
            linked_calls = [None] * len(function_calls)
            i = 0
            for function_call, flag in function_calls:
                function_name = function_call.split(".")
                if len(function_name) < 2:
                    continue
                function_name = function_name[1]
                paths = html_filepath.split("/")
                index = [i for i in range(len(paths)) if function_name in paths[i]]
                if len(index) == 0:
                    continue
                dot = ""
                if len(index) == 2:
                    dot = "."
                final_path = '<a href="{}./{}/{}_functional.html">{}</a>'.format(
                    dot, function_name, function_name, function_call.split()[1]
                )
                if flag:
                    linked_calls[i] = "of {}".format(final_path)
                else:
                    linked_calls[i] = "for {}".format(final_path)
                i += 1
            res = 0
            for i in range(len(function_call_indices)):
                if linked_calls[i]:
                    docstring_content = (
                        docstring_content[0 : function_call_indices[i][0] + res]
                        + linked_calls[i]
                        + docstring_content[function_call_indices[i][1] + res :]
                    )
                    res += len(linked_calls[i]) - (
                        function_call_indices[i][1] - function_call_indices[i][0]
                    )
            html_contents_modded = (
                html_contents_modded[0:docstring_start_index]
                + docstring_content
                + html_contents_modded[docstring_end_index:]
            )

    sub_str = '<dt class="field-odd">Parameters</dt>'
    indices = [
        i
        for i in range(len(html_contents_modded))
        if html_contents_modded.startswith(sub_str, i)
    ]
    for i in range(len(indices)):
        code_str = '<code class="xref py py-class docutils literal notranslate"><span class="pre">'
        if i == len(indices) - 1:
            end = len(html_contents_modded)
        else:
            end = indices[i + 1]
        code_indices = [
            x
            for x in range(indices[i], end)
            if html_contents_modded.startswith(code_str, x)
        ]
        for j in range(len(code_indices)):
            code_index = code_indices[j]
            code_end = (
                code_index + html_contents_modded[code_index:].find("</code>") + 7
            )
            code = html_contents_modded[code_index:code_end]
            if (
                "_DeviceArray" in code
                or "DeviceArray" in code
                or "ndarray" in code
                or "Tensor" in code
            ):
                if html_contents_modded[code_index - 2 : code_index] == ", ":
                    code_index -= 2
                html_contents_modded = (
                    html_contents_modded[0:code_index]
                    + '<doc-builder-tensor-placeholder>' * (code_end - code_index + 1)
                    + html_contents_modded[code_end + 1 :]
                )

    html_contents_modded = html_contents_modded.replace("<doc-builder-tensor-placeholder>", "")
    with open(html_filepath, "w") as file:
        file.write(html_contents_modded)


def modify_html_files(directory):
    # List all files and folders in the build directory
    items_in_dir = os.listdir(directory)

    # Get paths of each file in the build directory
    paths = [os.path.join(directory, item) for item in items_in_dir]

    # Recursively traverse all files
    for item in paths:
        if item[-5:] == ".html":
            modify_html_file(item)
        elif os.path.isdir(item):
            modify_html_files(item)


# All html files have been already developed with sphinx build, this script is aimed at modifications to those files.
modify_html_files("build")
print("\nParsed and corrected built html files\n")
