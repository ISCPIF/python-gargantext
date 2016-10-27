{% if list_corpora  %}
    {% for key, corpora in list_corpora.items %}
        <h2>
            <div class="row">
            <div class="col-md-1 content"></div>
                <span class="glyphicon glyphicon-cd" aria-hidden="true"></span>
                {{ key }}
        </h2>
                {% for corpus in corpora %}
                    <div id="corpus_{{corpus.id}}">
                        <div class="row">
                            <h4>
                                <div class="col-md-1 content"></div>
                                <div class="col-md-5 content">
                                    <a href="/projects/{{project.id}}/corpora/{{corpus.id}}">
                                        <span class="glyphicon glyphicon-file" aria-hidden="true"></span>
                                        {{corpus.name}}, {{ corpus.count }} documents {{ corpus.status_message }}
                                    </a>
                                </div>
                                <div class="col-md-3 content">
                                    <!--  -->
                                    {% for state in corpus.hyperdata.statuses %}
                                        {% ifequal state.action "Workflow" %}
                                            {% if state.complete %}

                                                <a href="/projects/{{project.id}}/corpora/{{corpus.id}}" title="View the corpus">
                                                    <button type="button" class="btn btn-default" aria-label="Left Align">
                                                          <span class="glyphicon glyphicon-eye-open" aria-hidden="true"></span>
                                                    </button>
                                                </a>

                                                <button type="button" class="btn btn-default yopla" data-container="body" data-toggle="popover" data-placement="bottom"  data-trigger="focus"
                                                    data-content="
                                                    <ul>
                                                        <li
                                                        onclick=&quot;
                                                                garganrest.metrics.update({{corpus.id}}, function(){alert('The corpus ({{corpus.name|escapejs}}) was updated')});
                                                                &quot;>
                                                            <a href='#'>Recalculate ngram metrics</a> <br/> (can take a little while)
                                                        </li>
                                                    </ul>
                                                    ">
                                                    <span class="glyphicon glyphicon-repeat" aria-hidden="true"
                                                    title='Recalculate ngram scores and similarities'></span>
                                                </button>
                                            {% endif %}

                                                <!-- TODO: delete non seulement si state.complete mais aussi si state.error -->
                                                <button type="button" class="btn btn-default" data-container="body" data-toggle="popover" data-placement="bottom"
                                                    data-content="
                                                    <ul>
                                                        <li
                                                        onclick=&quot;
                                                                garganrest.nodes.delete({{corpus.id}}, function(){$('#corpus_'+{{corpus.id}}).remove()});
                                                                $(this).parent().parent().remove();
                                                            &quot;>
                                                            <a href='#'>Delete this</a>
                                                        </li>
                                                    </ul>
                                                    ">
                                                    <span class="glyphicon glyphicon-trash" aria-hidden="true"
                                                    title='Delete this corpus'></span>
                                                </button>
                                        {% endifequal %}
                                    {% endfor %}
                                </div>
                                <div class="col-md-3 content">
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
                                                            <div class=" progress-bar progress-bar-striped
                                                                                        progress-bar-success
                                                                                 "
                                                                            role="progressbar" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100" style="width: 20%">
                                                                          <span>
                                                                              Upload
                                                                          </span>
                                                            </div>

                                                            {% for state in corpus.hyperdata.statuses %}

                                                                  <div class=" progress-bar progress-bar-striped
                                                                                    {% if state.complete %}
                                                                                        progress-bar-success
                                                                                        {% else %}
                                                                                        active
                                                                                    {% endif %}
                                                                                 "
                                                                            role="progressbar" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100" style="width: 20%">
                                                                          <span>
                                                                              {{ state.action }}
                                                                                    {% if not state.complete %}
                                                                                        Processing
                                                                                    {% endif %}

                                                                          </span>
                                                                  </div>

                                                            {% endfor %}
                                                        </div>
                                                    {% endif %}
                                                {% endif %}
                                            {% endifequal %}
                                    {% endfor %}
                                </div>
                                <div class="col-md-1 content"></div>
                            </h4>
                        </div>
                    </div>
                {% endfor %}
    {% endfor %}
{% endif %}
