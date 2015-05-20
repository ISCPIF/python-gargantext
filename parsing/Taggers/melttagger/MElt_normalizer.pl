#!/usr/bin/perl

binmode STDIN, ":utf8";
binmode STDOUT, ":utf8";
binmode STDERR, ":utf8";
use utf8;
use locale;

$do_not_load_lexicon=0;

while (1) {
  $_ = shift;
  if (/^-d$/) {$ngrams_file_dir = shift}
  elsif (/-nc$/) {$no_correction = 1}
  elsif (/^-nolex$/) {$do_not_load_lexicon = 1}
  elsif (/^-c$/) {$has_sxpipe_comments = 1}
  elsif (/^-l$/) {$lang = shift || die "Please provide a language code after option -l"}
  elsif (/^$/) {last}
  else {die "Unknown option '$_'"}
}

if ($lang eq "zzz" || $no_correction) {
  while (<>) {
    chomp;
    print $_."\n";
  }
  exit 0;
}

$ngrams_file_dir .= "/" unless $ngrams_file_dir eq "" || $ngrams_file_dir =~ /\/$/;

print STDERR "  NORMALIZER: Loading lexical information for language $lang...\n";

if (-d "$ngrams_file_dir") {
  unless ($do_not_load_lexicon) {
    if (-e "${ngrams_file_dir}lex") {
      open FILE, "${ngrams_file_dir}lex";
      binmode FILE, ":utf8";
      while (<FILE>) {
	chomp;
	s/(^|[^\\])#.*//;
	next if /^\s*$/;
	next if /^_/;
	/^(.*?)\t(.*?)\t(.*)$/ || next;
	$form = $1;
	$cat = $2;
	$ms = $3;
	$form =~ s/__.*$//;
	if ($lang eq "fr") {
	  $adj_nom_voyelle{$form} = 1 if ($cat =~ /^(adj|nom)/ && $form =~ /^[aeiuoé]/);
	  $verbe_voyelle{$form} = 1 if ($cat eq "v" && $form =~ /^[aeiuoé]/);
	  $inf{$form} = 1 if ($cat eq "v" && $ms eq "W");
	  $verbe_1s{$form} = 1 if ($cat eq "v" && $ms =~ /1/);
	  $lex_final_e{$form} = 1 if $form =~ /e$/;
	  $lex_final_s{$form} = 1 if $form =~ /s$/;
	  $lex_final_t{$form} = 1 if $form =~ /t$/;
	}
	$lex{$form} = 1;
      }
      close FILE;
    
      if ($lang eq "fr") {
	for (sort {length($b) <=> length($a)} keys %adj_nom_voyelle) {
	  if (!defined($lex{"l".$_})) {
	    $glueddet{"l".$_} = "{l$_◀l'} l' {} $_";
	  }
	  if (!defined($lex{"d".$_})) {
	    $glueddet{"d".$_} = "{d$_◀d'} d' {} $_";
	  }
	}
	
	for (sort {length($b) <=> length($a)} keys %verbe_voyelle) {
	  if (!defined($lex{"l".$_})) {
	    $gluedclit{"s".$_} = "{s$_◀s'} s' {} $_";
	  }
	  if (!defined($lex{"d".$_})) {
	    $gluedclit{"n".$_} = "{n$_◀n'} n' {} $_";
	  }
	}
	
	for (sort {length($b) <=> length($a)} keys %inf) {
	  if (!defined($lex{"2".$_})) {
	    $glued2{"2".$_} = "{2$_◀2=de} de {} $_";
	  }
	}
	
	for (sort {length($b) <=> length($a)} keys %verbe_1s) {
	  if (!defined($lex{"j".$_})) {
	    $gluedj{"j".$_} = "{j$_◀j'} j' {} $_";
	  }
	  if (!defined($lex{"J".$_})) {
	    $gluedj{"J".$_} = "{J$_◀J'} J' {} $_";
	  }
	}
      }
    } else {
      print STDERR "  NORMALIZER: No normalization lexical information found for language '$lang'. Skipping\n";
    }
  }

  print STDERR "  NORMALIZER: Loading lexical information for language $lang: done\n";
  
  print STDERR "  NORMALIZER: Loading replacement patterns (${ngrams_file_dir}ngrams...)\n";
  if (-e "${ngrams_file_dir}ngrams") {
    open NGRAMS, "<${ngrams_file_dir}ngrams" || die $!;
    binmode NGRAMS, ":utf8";
    while (<NGRAMS>) {
      /^([^_\t][^\t]*)\t([^\t]+)(\t|$)/ || next;
      $in = $1;
      $out = $2;
      $newout = "";
      if ($out =~ /\$\d/ || $in =~ /\\/) {
	$in =~ s/(\[\^[^ \]]*) /\1‗/g;
      }
      @in = split / /, $in;
      @out = split / /, $out;
      my $j = 1;
      if ($#in ne $#out) {
	print STDERR "  NORMALIZER: Ignoring replacement /$in/$out/ found (different input and output token number)\n";
      } else {
	for $i (0..$#in) {
	  if ($out =~ /\$\d/ || $in =~ /\\/) {
	    while ($in[$i] =~ s/\(.*?\)/\$$j/) {$j++;}
	  }
	  $newout .= "{$in[$i]◀".($#in+1)."} $out[$i] ";
	}
      }
      $newout =~ s/ $//;
      while ($newout =~ s/(}[^{]*) /$1 {} /g){}
      if ($newout =~ /\$\d/ || $in =~ /\\/) {
	$ngrams{qr/$in/} = $newout;
      } else {
	$ngrams{quotemeta($in)} = $newout;
      }
    }
    close NGRAMS;
  } else {
    print STDERR "  NORMALIZER: No replacement patterns found for language '$lang'. Skipping\n";
  }
  print STDERR "  NORMALIZER: Loading replacement patterns: done\n";
} else {
  print STDERR "  NORMALIZER: No replacement patterns available for language '$lang'. Skipping\n";
}


print STDERR "  NORMALIZER: Normalizing...\n";
while (<>) {
  chomp;
  $_ = "  $_  ";
  s/}\s*_/} _/g;
  $is_maj_only = 0;
  $tmp = $_;
  $tmp =~ s/◀.*?}/}/g;
  $tmp =~ s/{([^{}]+)} _[^ ]+/$1/g;
  if ($tmp=~/^[^a-zâäàéèêëïîöôüûùÿ]+$/ && $tmp=~/[A-Z]{5,}/ && length($tmp) > 10) {
    $is_maj_only = 1;
    $_ = lc($_);
    s/}\s*_(url|smiley|email|date[^ ]*|time|heure|adresse|underscore|acc_[of])/"} _".uc($1)/ge;
    s/(-[lr][rcs]b-)/uc($1)/ge;
  }
  if ($has_sxpipe_comments) {
    s/{([^{}]+)} *\1( |$)/\1\2/g;
  }
  for $ngram (sort {(($b=~s/([  ])/\1/g) <=> ($a=~s/([  ])/\1/g)) || (length($b) <=> length($a))} keys %ngrams) {
    $t = $ngrams{$ngram};
    $t =~ s/ / /g;
    $ngram =~ s/ / /g;
    $ngram =~ s/‗/ /g;
    if ($t =~ /\$/) {
      while (/(?<=[^}]) $ngram /) {
	@v = ();
	$v[1] = $1;
	$v[2] = $2;
	$v[3] = $3;
	$v[4] = $4;
	$v[5] = $5;
	$v[6] = $6;
	$v[7] = $7;
	$v[8] = $8;
	$v[9] = $9;
	$tmp = $t;
	for $i (1..9) {
	  $tmp =~ s/\$$i/$v[$i]/g;
	}
	s/(?<=[^}]) $ngram / $tmp /;
      }
    } else {
      s/(?<=[^}]) $ngram / $t /g;
    }
  }
  $tmp = $_;
  $_ = "";
  while ($tmp =~ s/^ *((?:{.*?} )?)(.*?) //) {
    $orig = $1;
    $target = $2;
    $tmptarget = $target;
    if ($lang eq "fr") {
      if ($orig eq "" && length($target) >= 3 && $target !~ /[{}]/ && !defined($lex{$target}) && defined($glueddet{$target})) {
	$_ .= $glueddet{$target}." ";
      } elsif ($orig eq "" && length($target) >= 3 && $target !~ /[{}]/ &&!defined($lex{$target}) && defined($gluedclit{$target})) {
	$_ .= $gluedclit{$target}." ";
      } elsif ($orig eq "" && length($target) >= 3 && $target !~ /[{}]/ &&!defined($lex{$target}) && defined($glued2{$target})) {
	$_ .= $glued2{$target}." ";
      } elsif ($orig eq "" && length($target) >= 3 && $target !~ /[{}]/ &&!defined($lex{$target}) && defined($gluedj{$target})) {
	$_ .= $gluedj{$target}." ";
      } elsif ($orig eq "" && length($target) >= 2 && $target =~ /^[a-zâäàéèêëïîöôüûùÿ]+$/ && !defined($lex{$target}) && defined($lex_final_s{$target."s"})) {
	$_ .= "{$target◀s} ${target}s ";
      } elsif ($orig eq "" && length($target) >= 2 && $target =~ /^[a-zâäàéèêëïîöôüûùÿ]+$/ &&!defined($lex{$target}) && defined($lex_final_t{$target."t"})) {
	$_ .= "{$target◀t} ${target}t ";
      } elsif ($orig eq "" && length($target) >= 2 && $target =~ /^[a-zâäàéèêëïîöôüûùÿ]+$/ &&!defined($lex{$target}) && defined($lex_final_e{$target."e"})) {
	$_ .= "{$target◀e} ${target}e ";
      } elsif ($orig eq "" && length($target) >= 2 && $target =~ /^[a-zâäàéèêëïîöôüûùÿ]+$/ &&!defined($lex{$target}) && $tmptarget =~ s/è/é/g && defined($lex{$tmptarget})) {
	$_ .= "{$target◀èé} $tmptarget ";
      } elsif ($orig eq "" && length($target) >= 2 && $target =~ /^[a-zâäàéèêëïîöôüûùÿ]+$/ &&!defined($lex{$target}) && $tmptarget =~ s/é$/ait/g && defined($lex{$tmptarget})) {
	$_ .= "{$target◀éait} $tmptarget ";
      } elsif ($orig eq "" && length($target) >= 2 && $target !~ /[{}]/ &&!defined($lex{$target}) && ($tmptarget =~ s/(^|[^w])([w\.])\2\2([^w]|$)/\1 \2 \2 \2 \3/g || 1)
	       && $tmptarget =~ s/([^0-9\.])(?:\1){2,}/\1/g) {
	$tmptarget =~ s/ ([.]) \1 \1 /\1\1\1/g;
	if ($tmptarget =~ /^(.)(.)/ && $1 eq uc($2)) {
	  $tmptarget =~ s/^(.)./\1/;
	}
	$_ .= "{$target◀etir} $tmptarget ";
      } elsif ($orig eq "" && length($target) >= 2 && $target =~ /^[a-zâäàéèêëïîöôüûùÿ]+$/ &&!defined($lex{$target}) && $tmptarget =~ /^(.*)k$/ && defined($lex{$1.'que'})) {
	$tmptarget =~ s/k$/que/;
	$_ .= "{$target◀kque} $tmptarget "; # on ne vérifie même pas que ce soit dans le lex
      } elsif ($orig eq "" && length($target) >= 2 && $target =~ /^[a-zâäàéèêëïîöôüûùÿ]+$/ &&!defined($lex{$target}) && $target =~ /[aeé]men$/) {
	$_ .= "{$target◀ment} ${target}t "; # on ne vérifie même pas que ce soit dans le lex
      } else {
	$_ .= $orig.$target." ";
      }
    } else {
      $_ .= $orig.$target." ";
    }
  }
  if ($is_maj_only) {
    s/{([^}◀]+)/"{".uc($1)/ge;
    s/^ *([^{} ]+)/" {".uc($1)."◀lc} ".$1/ge;
    s/(?<=[^}]) ([^{} ]+)(?= )/" {".uc($1)."◀lc} ".$1/ge;
  }
  s/{([^}◀]+)(?:◀[^}]*)} \1 /\1 /g;
  s/{([LDJSldsj])◀1} [LDJldsj]' +$/\1/;
  s/ +$//;
  s/^ +//;

  s/◀[^}]*}/}/g; # à sauter si on veut garder les indicateurs de type de correction

  print "$_\n";
}
print STDERR "  NORMALIZER: Normalizing: done\n";
