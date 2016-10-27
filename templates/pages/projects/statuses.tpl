{% for state in corpus.hyperdata.statuses %}
        {% ifequal state.action "Workflow" %}
            {% if state.complete %}
            <span class="glyphicon glyphicon-ok" aria-hidden="true"></span>

            {% else %}
                {% if state.error %}
                    <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
                    {{ state.error }}
                {% else %}
                    <div class="progress">
                        {% for state in corpus.hyperdata.statuses %}
                            {% if state.action != "Workflow" %}
                              <div class=" progress-bar progress-bar-striped
                                                {% if state.complete %}
                                                    progress-bar-success
                                                    {% else %}
                                                    active
                                                {% endif %}
                                             "
                                        role="progressbar" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100" style="width: 25%">
                                      <span>
                                          {{ state.action }}
                                                {% if state.complete %}
                                                    Ok
                                                    {% else %}
                                                    Processing
                                                {% endif %}

                                      </span>
                              </div>
                            {% endif %}
                        {% endfor %}
                    </div>
                {% endif %}
            {% endif %}
        {% endifequal %}
{% endfor %}
function manageStatus(statuses){
  status_bar = ""
  status_bar += '<div class="progress">'
  statuses.forEach(function (status){
    if (status["action"] == "Workflow"){
      if (status["complete"]){
        status_bar += '<span class="glyphicon glyphicon-ok pull-right" aria-hidden="true"></span></div>'
        return status_bar;
      };
      else if (status["error"]) {
        status_bar += '<span class="glyphicon glyphicon-exclamation-sign pull-right" aria-hidden="true"></span></div>'
        return status_bar;
      };
      else{

      };
    };
    else{
          status_bar +='<div class=" progress-bar progress-bar-striped'
          if (status["complete"]){
            status_bar +='progress-bar-sucess'
          };
          else{
            status_bar +='active'
          };

          status_bar+= '" role="progressbar" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100" style="width: 25%"> <span>'
          if (status["action"]){
            if (status["complete"]){
              status_bar+= " OK </span></div>"

            };
            else{
              status_bar+= " Processing </span>"
            };
          }
        });
      }
      }
  })
  status_bar+="</div>"
  return status_bar
};
