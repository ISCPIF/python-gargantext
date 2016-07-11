<?php

class scanTree {

    public $root;
    public $folders = array();
    public $gexf_folder = array();

    public function __construct($rootpath = "") {
        $this->root = $rootpath;
    }

    public function getDirectoryTree($dir) {
        $folder = array();
        $dbs = array();
        $gexfs = array();
        $dataFolder = $this->root . $dir;
        $files = scandir($dataFolder);
        foreach ($files as $f) {
            if ($f != "." and $f != ".." and $f[strlen($f) - 1] != "~") {
                if (is_dir($dataFolder . "/" . $f)) {
                    //pr("Dir: ".$f);
                    $subfolder = $f;
                    $this->getDirectoryTree($dir . "/" . $subfolder);
                } else {
                    //pr("File: ".$f);
                    if ((strpos($f, '.gexf')))
                        array_push($gexfs, $f);
                    if ((strpos($f, '.db')) or (strpos($f, '.sqlite')) or (strpos($f, '.sqlite3')))
                        array_push($dbs, $f);
                    if (!$folder[$dir]["gexf"] or !$folder[$dir]["dbs"])
                        $folder[$dir] = array();
                    $folder[$dir]["gexf"] = $gexfs;
                    $folder[$dir]["dbs"] = $dbs;
                    if ((strpos($f, '.gexf'))) {
                        $this->gexf_folder[$dir . "/" . $f] = "";
                    }
                }
            }
        }
        if ($folder[$dir]["gexf"]) {
            foreach ($folder[$dir]["gexf"] as $g) {
                $this->gexf_folder[$dir . "/" . $g] = count($this->folders);
            }
        }
        array_push($this->folders, $folder);
    }

}

?>
