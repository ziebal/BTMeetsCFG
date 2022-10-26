import inspect
from jinja2 import Template
import datetime
from binary_template_converter.source.BTMeetsCFG.oldVersion.global_defines import GlobalDefines


class BinaryTemplateGeneratorSpecific:
    def __init__(self, parsing_table, token_length):
        self.__max_size = 1000
        self.__eof_chance = 0.5
        self.__globals = []
        self.__start_key = None
        self.__parsing_table = parsing_table
        self.__token_length = token_length

    def __generate_header_code(self, name, switch_statement, select_statement, is_start_key):
        # TODO remove debug print
        print("Header Data:", name)

        template = """\
            {%- if is_start_key %}
            struct {{ name }} {
            local string follow[0];
            local int size = 0;
            {%- else %}
            struct {{ name }}(string follow[], int size, int epsilon1) {
            {%- endif %}
            {% filter indent(width=4) %}
            {{ select }}
            
            Printf("{{ name }} did read: %s\\n", selection);
            {{ switch }}    
            {%- endfilter %}
            };
        """
        tmp = inspect.cleandoc(template)
        j2_template = Template(tmp)

        result = j2_template.render({
            "name": name,
            "switch": switch_statement,
            "select": select_statement,
            "is_start_key": is_start_key
        })

        # TODO remove debug print
        # print("Result:")
        # print(result)

        return result

    def __generate_switch_code(self, switch_data):
        # TODO remove debug print
        # print("Switch Data:")
        # print(json.dumps(switch_data, indent=2))

        template = """switch (selection) {
            {% for key in switch_data -%}
            case "{{ switch_data[key]["name"] }}":
                // TODO this is kinda broken
                local int epsilon = 1;
                {% for symbol in switch_data[key]["rule"] %}
                // debug information: 
                // {{ symbol }}
                // follow:
                {%- for follow in symbol.follow %}
                // {{ follow }}
                {%- endfor %}
                // first: 
                {%- for first in symbol.first %}
                // {{ first }}
                {%- endfor %}
                {%- if symbol.token == "" %}
                // epsilon entries are treated as fallthrough
                {%- elif symbol.label == "terminal" %}
                char {{ symbol.uid.lower() }}[{{ length }}] = { "{{ symbol.token }}" }; 
                {%- else %}
                // {{ symbol.token }} - expected follow values: {% for follow in symbol.follow %}{{follow.token}} {% endfor %}
                {% if symbol.include_parent_follow %}
                local int combined_follow_size = size + {{ symbol.follow_size }};
                local string follow_new[combined_follow_size];
                local int i;
                for (i = 0; i < size; i++)
                    follow_new[i] = follow[i];
                {% for follow in symbol.follow %}
                follow_new[{{ loop.index0 }} + size] = "{{follow.token}}";
                {% endfor %} 
                {{ symbol.uid }} {{ symbol.uid.lower() }}(follow_new, combined_follow_size, {% if symbol.follow_contained_epsilon %}1{% else %}0{% endif %}); // {{ symbol.token }}
                {% else %}
                //if (epsilon) {
                    local string follow_new[] = {
                        // Debug: {{ symbol }}
                        {% for follow in symbol.follow %}{% if "FOLLOW(" in follow %}/* TODO FOLLOW */{% else %}"{{follow.token}}",{% endif %}{% endfor %} 
                        // {% for first in symbol.first %}"{{first.token}}",{% endfor %}
                        "NULL"
                    };
                    {{ symbol.uid }} {{ symbol.uid.lower() }}(follow_new, {{ symbol.follow_size }}, {% if symbol.follow_contained_epsilon %}1{% else %}0{% endif %}); // {{ symbol.token }}
                //} else {
                //    local string follow_new[] = {
                //        "NULL"
                //    };
                //    {{ symbol.uid }} {{ symbol.uid.lower() }}(follow_new, 0); // {{ symbol.token }}
                //}
                {% endif %}
                {%- endif %}
                epsilon = {% if symbol.follow_contained_epsilon %}1{% else %}0{% endif %};
                {% endfor %}
                break;  
            {% endfor %}
        }
        """
        tmp = inspect.cleandoc(template)
        j2_template = Template(tmp)

        result = j2_template.render({
            "switch_data": switch_data,
            "length": self.__token_length
        })

        # TODO remove debug print
        # print("Result:")
        # print(result)

        return result

    def __generate_select_code(self, select_data, select_size, is_start_key):
        # TODO remove debug print
        # print("Select Data:", select_data)

        template = """
            // Debug Information:
            {% for entry in select -%}
            // {{ entry }}
            {% endfor %}
            local char selection[{{ length }}];
            local int pref_val_size = {{ select_size }};
            {%- if start %}
            local string pref_val[] = { {% for symbol in select -%}{% if symbol["token"] != "" %}"{{ symbol["token"] }}",{% endif %}{% endfor %}};
            ReadBytes(selection, FTell(), {{ length }}, pref_val);
            {%- else %}
            
            if (epsilon1) {
                local string pref_val[pref_val_size + size];
                {% for symbol in select %}
                pref_val[{{loop.index0}}] = "{{ symbol["token"] }}";
                {%- endfor %}
                
                local int i;
                for (i = pref_val_size; i < pref_val_size + size; i++)
                    pref_val[i] = follow[i - pref_val_size];
                ReadBytes(selection, FTell(), {{ length }}, pref_val);
            } else {
                local string pref_val[pref_val_size];
                {% for symbol in select %}
                pref_val[{{loop.index0}}] = "{{ symbol["token"] }}";
                {%- endfor %}
                ReadBytes(selection, FTell(), {{ length }}, pref_val);
            }
            {%- endif %}
        """
        tmp = inspect.cleandoc(template)
        j2_template = Template(tmp)

        result = j2_template.render({
            "select": select_data,
            "start": is_start_key,
            "select_size": select_size,
            "length": self.__token_length
        })

        # TODO remove debug print
        # print("Result:")
        # print(result)

        return result

    def __generate_code(self, code, ct):

        template = """\
                    // Generation time: {{ time }}
                    {% for entry in globals %}
                    struct {{ entry }}(string follow[], int size){};
                    {%- endfor %}
                    {% for entry in code %}
                    {{ entry }}
                    {% endfor %}
                    SetEvilBit(false);
                    {{ start }} {{ start.lower() }};
                """
        tmp = inspect.cleandoc(template)
        j2_template = Template(tmp)

        result = j2_template.render({
            "globals": self.__globals,
            "start": self.__start_key,
            "code": code,
            "time": ct
        })

        # TODO remove debug print
        # print("Result:")
        # print(result)

        return result

    def __generate_globals_and_start(self):
        distinct_keys = self.__parsing_table.get_distinct_keys()
        for key in distinct_keys:
            normalized_name = GlobalDefines.normalize(key, "non_terminal")
            if key != "<start>":
                self.__globals.append(normalized_name)
            else:
                self.__start_key = GlobalDefines.normalize(key, "non_terminal")

    def generate_code(self, code):
        ct = datetime.datetime.now()
        self.__generate_globals_and_start()
        code_blocks = []
        for key, value in code.get_iterable().items():
            select_code = self.__generate_select_code(value["select"], value["select_size"], value["name"] == self.__start_key)
            switch_code = self.__generate_switch_code(value["switch"])
            header_code = self.__generate_header_code(value["name"], switch_code, select_code, value["name"] == self.__start_key)
            code_blocks.append(header_code)

        return self.__generate_code(code_blocks, ct)
