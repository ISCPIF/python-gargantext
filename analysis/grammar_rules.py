        # Grammars rules
        #'^((VBD,|VBG,|VBN,|CD.?,|JJ.?,|\?,){0,2}?(N.?.?,|\?,)+?(CD.,)??)+?((PREP.?|DET.?,|IN.?,|CC.?,|\?,)((VBD,|VBG,|VBN,|CD.?,|JJ.?,|\?,){0,2}?(N.?.?,|\?,)+?)+?)*?$'



tina = r"""
          NP:
               {^(<VBD,|VBG,|VBN,|CD.?,|JJ.?,|\?,>{0,2}?<N.?.?,|\?,>+?<CD.,>??)+?((PREP.?|DET.?,|IN.?,|CC.?,|\?,)((VBD,|VBG,|VBN,|CD.?,|JJ.?,|\?,){0,2}?(N.?.?,|\?,)+?)+?)*?$}
        """

jj_nn = r"""
         NP:  
                {<JJ.*>*<NN.*|>+<JJ.*>*}
        """

nn_prp_nn = r"""
         NP:  
                {<NN.?>+<PRP.?>+<DT.?>*<NN.?>+}
        """

mix = r"""
          NP: 
                {<JJ.?>*<NN.?|>+<JJ.?>*<PRP.?>*<DT.?>*<JJ.?>*<NN.?>*<JJ.?>*}

        """

vv = r"""
         NP:  
                {<VV.*>+}
        """

