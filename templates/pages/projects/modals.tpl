<div class="modal fade" id="stack1" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
                <h3>Query to PubMed</h3>
            </div>
            <div class="modal-body">
                <p>One fine body…</p>
                <input id="daquery" type="text" class="input-lg" data-tabindex="2">
                <a onclick="getGlobalResults();" class="btn">Scan</a>
                <div id="results"></div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                <button onclick="doTheQuery();" disabled id="id_thebutton" type="button" class="btn btn-primary">Explore a sample!</button>
            </div>
        </div><!-- /.modal-content -->
    </div><!-- /.modal-dialog -->
</div><!-- /.modal -->

<!-- Modal -->
<div class="modal fade" id="addcorpus" tabindex="-1" role="dialog" aria-labelledby="myModalLabel2" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>

                <h3>Add a Corpus <a href="https://gogs.iscpif.fr/humanities/faq_gargantext/wiki/FAQ#import--export-a-dataset">
                  <span class="glyphicon glyphicon-question-sign" aria-hidden="true"></span>
                </a>
              </h3>
            </div>
            <div class="modal-body">
              <!-- FAQ -->
                <form id="id_form" enctype="multipart/form-data" action="/projects/{{project.id}}/" method="post">
                    {% csrf_token %}
                    <table cellpadding="5">


                        {% for field in form %}
                        <tr>
                            <th>{{field.label_tag}}</th>
                            <td>
                                {{ field.errors }}
                                {{ field }}
                                {% if field.name == 'name' %}
                                <span onclick="getGlobalResults(this);" id="scanpubmed"></span>
                                <div id="theresults"></div>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                        <tr>
                            <th></th>
                            <td>
                                <div id="pubmedcrawl" style="visibility: hidden;">
                                    Do you have a file already? &nbsp;
                                    <input type="radio" id="file_yes" name="file1" onclick="FileOrNotFile(this.value);" class="file1" value="true" checked> Yes </input>
                                    <input type="radio" id="file_no" name="file1" onclick="FileOrNotFile(this.value);" class="file1" value="false"> No </input>
                                </div>
                            </td>
                        </tr>
                    </table>
                </form>
                <div class="modal-footer">
                    <!-- <div id="pubmedcrawl" align="right" style="visibility: hidden;"><a data-toggle="modal" href="#stack1">&#10142; Query directly in PubMed</a></div> -->
                    <button type="button" class="btn btn-default" data-dismiss="modal">
                        <span class="glyphicon glyphicon-remove" aria-hidden="true" ></span>
                        Close
                    </button>
                    <button onclick='bringDaNoise();' id="submit_thing" disabled class="btn btn-primary" >
                        <span class="glyphicon glyphicon-ok" aria-hidden="true" ></span>
                        Process this!
                    </button><span id="simpleloader"></span>
                </div>
            </div>
        </div><!-- /.modal-content -->
    </div><!-- /.modal-dialog -->
</div><!-- /.modal -->
<!-- Modal -->
<div id="wait" class="modal fade">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
    <h2 class="modal-title"><h2><span class="glyphicon glyphicon-info-sign" aria-hidden="true"></span>  Uploading corpus...</h2>
  </div>
  <div class="modal-body">
    <h5>
    Your file has been uploaded !
    Gargantext need some time to eat it.
    Duration depends on the size of the dish.
  </h5>
  </div>
  <div class="modal-footer">
    <button type="button" class="btn btn-secondary" data-dismiss="modal">Continue on Gargantext</button>
  </div>
</div><!-- /.modal-content -->
</div><!-- /.modal-dialog -->
</div><!-- /.modal -->
