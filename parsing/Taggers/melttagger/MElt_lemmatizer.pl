#!/usr/bin/perl

use utf8;
use locale;
binmode STDIN, ":utf8";
binmode STDOUT, ":utf8";
binmode STDERR, ":utf8";
use DBI;
use Encode;

my $datadir = ".";
my $language = "";
my $model = "";
my $lexfile = "";
my $it_mapping = 0;
my $flag_unknowns = "*";
my $verbose = 0;
my $multiple_lemmas = 0;
my $silent = 0;

while (1) {
  $_ = shift;
  if (/^-l$/) {$language = shift;}
  elsif (/^-m$/) {$model = shift;}
  elsif (/^-nv$/) {$silent = 1;}
  elsif (/^-l?db$/) {$dbfile = shift;}
  elsif (/^-nfu$/) {$flag_unknowns = "";}
  elsif (/^-v$/) {$verbose = 1;}
  elsif (/^-itmapping$/) {$it_mapping = 1;}
  elsif (/^-lcl$/) {$lower_case_lemmas = 1;}
  elsif (/^-ml$/) {$multiple_lemmas = 1;}
  elsif (/^-h$/ || /^--?help^/) {
    print STDERR <<END;
Usage: MElt_lemmatizer.pl [ -l language | -m model | -lex lexicon ] [ -nfu ] [ -itmapping ] [ -lcl ] < input > output
Input:	POS-tagged text in Brown format. The text *must* have been tagged using MElt, as this lemmatizer is based
	on the (external) lexicon used by a particular MElt model and on the tags assigned by MElt using this model
	Brown format: word1/pos1 word2/pos2 ... wordn/posn		(newline = new sentence)
Output:	word1/pos1/lemma1 word2/pos2/lemma2 ... wordn/posn/lemman	(newline = new sentence; lemmas for words
	                                                                unknown to the lexicon are prefixed with '*')
Options:
	-l language	Use the lexicon of the default MElt model for language 'language'
	-m model	Use the lexicon of the MElt model to be found in the directory 'model'
	-lex lexicon	Use the lexicon provided
	-v		Verbose (outputs information about the options used on STDERR before lemmatizing)
	-nfu		Do not prefix lemmas for forms unknown to the lexicon with the character '*'
	-lcl		Output all lemmas in lowercase
	-itmapping	Triggers special conversion and adaptation rules for Italian
	-h		Print this
END
    exit(0);
  }
  elsif (/^$/) {last}
}

if ($lang eq "it") {$itmapping = 1}

if ($dbfile eq "") {
  if ($model ne "") {
    if ($language ne "") {
      die "Error: options -l and -m can not be used simultaneously";
    }
  } else {
    if ($language eq "") {
      $language = "fr";
    }
    $model = $datadir."/".$language;
  }
  $dbfile = $model."/lemmatization_data.db";
} else {
  if ($language ne "" || $model ne "") {
    die "Error: option -lex can not be used with options -l or -m";
  }
}

if ($verbose) {
  print STDERR "Lemmatization database used:	$dbfile\n";
  if ($flag_unknowns eq "") {
    print STDERR "Lemmas for forms unknown to the lexicon are not prefixed by any special character\n" ;
  } else {
    print STDERR "Lemmas for forms unknown to the lexicon are prefixed with the character '$flag_unknowns'\n" ;
  }
  print STDERR "Lemmas are lowercased\n" if ($lower_case_lemmas);
  print STDERR "Special mappings for Italian activated\n" if ($it_mapping);
}

my $dbh = DBI->connect("dbi:SQLite:$dbfile", "", "", {RaiseError => 1, AutoCommit => 0});
my $sth_cfl=$dbh->prepare('select lemma from cat_form2lemma where cat=? and form=?');
my $sth_cfslsc1=$dbh->prepare('select lemmasuff from cat_formsuff_lemmasuff2count where cat=? and formsuff=? limit 1');
my $sth_cfslsc2=$dbh->prepare('select lemmasuff from cat_formsuff_lemmasuff2count where cat=? and formsuff=? order by count limit 1');
my $sth_cfslsc3=$dbh->prepare('select lemmasuff from cat_formsuff_lemmasuff2count where cat=? and formsuff=?');


%equiv = (
	  "--RBR--" => ")",
	  "--LBR--" => "(",
	  "--RRB--" => ")",
	  "--LRB--" => "(",
);

print STDERR "  LEMMATIZER: Lemmatizing...\n" unless $silent;

my %get_cat_form2lemma_cache;
my %includes_data_for_cat_formsuff_cache;
my %get_best_lemmasuffs_cache;
my %get_all_lemmasuffs_cache;

while (<>) {
  chomp;
  s/^\s+//;
  s/\s+$//;
  if (/^$/) {
    print "\n";
    next;
  }
  @result = ();
  s/$/ /;
  while (s/^ *((?:\[\|.*?\|\] *)?(?:\( *)?(?:{.*?} *)?)([^{ ][^ ]*?)\/([^\/ \)\|]+)((?: *[\|\)][\|\(\)]*)?) +([^ \|\)]|[\|\)][^ \|\)]|$)/$5/) {
    $comment = $1;
    $token = $2;
    $cat = $3;
    $post = $4;
    $postcat = "";
    if ($cat =~ s/(-UNK.*)$//) {
      $postcat = $1;
    }
    $lemma = "";
    if (get_cat_form2lemma($cat,$token) ne "") {
      push @result, "$comment$token/$cat$postcat/".get_cat_form2lemma($cat,$token);
    } elsif (get_cat_form2lemma($cat,lc($token)) ne "") {
      push @result, "$comment$token/$cat$postcat/".get_cat_form2lemma($cat,lc($token));
    } elsif (get_cat_form2lemma($cat,$equiv{$token}) ne "") {
      push @result, "$comment$token/$cat$postcat/".get_cat_form2lemma($cat,$equiv{$token});
    } elsif ($it_mapping && $token !~ /^[A-ZÉ]/ && $token =~ /^(.*?)(lo|la|mi|ne|gli|si|li|le)$/ && get_cat_form2lemma(VERB,lc($1)) ne "" && get_cat_form2lemma(PRON,lc($2)) ne "") {
      if ($cat ne "PRON") {
	push @result, "$comment$token/VERB$postcat/".get_cat_form2lemma(VERB,lc($1));
      } elsif ($cat eq "PRON") {
	push @result, "$comment$token/$cat$postcat/".get_cat_form2lemma($cat,lc($2));
      }
    } elsif ($it_mapping && $token !~ /^[A-ZÉ]/ && $token =~ /^(.*?)(lo|la|mi|ne|gli|si|li|le)$/ && get_cat_form2lemma(VERB,lc($1."e")) ne "" && get_cat_form2lemma(PRON,lc($2)) ne "") {
      if ($cat ne "PRON") {
	push @result, "$comment$token/VERB$postcat/".get_cat_form2lemma(VERB,lc($1."e"));
      } elsif ($cat eq "PRON") {
	push @result, "$comment$token/$cat$postcat/".get_cat_form2lemma($cat,lc($2));
      }
    } elsif ($it_mapping && $token !~ /^[A-ZÉ]/ && $token =~ /^(.*?)(.)(lo|la|mi|ne|gli|si|li|le)$/ && get_cat_form2lemma(VERB,lc($1.$2.$2."e")) ne "" && get_cat_form2lemma(PRON,lc($3)) ne "") {
      if ($cat ne "PRON") {
	push @result, "$comment$token/VERB$postcat/".get_cat_form2lemma(VERB,lc($1.$2.$2."e"));
      } elsif ($cat eq "PRON") {
	push @result, "$comment$token/$cat$postcat/".get_cat_form2lemma($cat,lc($3));
      }
    } elsif ($it_mapping && $token !~ /^[A-ZÉ]/ && $token =~ /^(.*)[ai]$/ && $cat =~ /^(NOUN|ADJ|PRON)$/) {
      if ($lower_case_lemmas) {
	push @result, "$comment$token/$cat$postcat/".lc($1)."o";
      } else {
	push @result, "$comment$token/$cat$postcat/$1o";
      }
    } else {
      if ($token !~ /^[A-ZÉ]/) {
	$token_suff = $token;
	$token_pref = "";
	while ($token_suff =~ s/^(.)(?=.)//) {
	  $token_pref .= $1;
	  if (includes_data_for_cat_formsuff($cat,$token_suff)) {
	    if ($multiple_lemmas) {
	      $lemma = get_all_lemmasuffs($cat,$token_suff,$token_pref)
	    } else {
	      $lemma = get_best_lemmasuffs($cat,$token_suff,$token_pref);
	    }
	    last;
	  }
	}
      }
      if ($lemma eq "") {$lemma = $token}
      if ($lower_case_lemmas) {
	push @result, "$comment$token/$cat$postcat/$flag_unknowns".lc($lemma);
      } else {
	push @result, "$comment$token/$cat$postcat/$flag_unknowns".$lemma;
      }
    }
  }
  $what_remains = $_;
  $_ = join(" ",@result);
  if ($what_remains =~ /^(\[\|.*?\|\])/) {
    $_ .= $1;
  }
  $what_remains =~ s/^\s*//;
  die $what_remains if ($what_remains ne "");
  print $_.$post."\n";
}

print STDERR "  LEMMATIZER: Lemmatizing: done\n" unless $silent;

sub get_cat_form2lemma {
  my $cat = shift;
  my $form = shift;
  if (defined($get_cat_form2lemma_cache{$cat}{$form})) {
    return $get_cat_form2lemma_cache{$cat}{$form};
  }
  $sth_cfl->execute($cat,$form);
  my %results = ();
  while (my $value = $sth_cfl->fetchrow) {
    $results{Encode::decode("utf8",$value)} = 1;
  }
  $sth_cfl->finish;
  my $result = (join "|", sort {$a cmp $b} keys %results);
  $get_cat_form2lemma_cache{$cat}{$form} = $result;
  return $result;
}

sub includes_data_for_cat_formsuff {
  my $cat = shift;
  my $formsuff = shift;
  if (defined($includes_data_for_cat_formsuff_cache{$cat}{$formsuff})) {
    return $includes_data_for_cat_formsuff_cache{$cat}{$formsuff};
  }
  $sth_cfslsc1->execute($cat,$formsuff);
  my $result = 0;
  while (my $value = $sth_cfslsc1->fetchrow) {
    $result = 1;
    last;
  }
  $sth_cfslsc1->finish;
  $includes_data_for_cat_formsuff_cache{$cat}{$form} = $result;
  return $result;
}

sub get_all_lemmasuffs {
  my $cat = shift;
  my $form = shift;
  my $token_pref = shift;
  if (defined($get_all_lemmasuffs_cache{$cat}{$form})) {
    return $get_all_lemmasuffs_cache{$cat}{$form};
  }
  $sth_cfslsc3->execute($cat,$form);
  my %results = ();
  while (my $value = $sth_cfslsc3->fetchrow) {
    $results{$token_pref.Encode::decode("utf8",$value)} = 1;
  }
  $sth_cfslsc3->finish;
  my $result = (join "|", sort {$a cmp $b} keys %results);
  $get_all_lemmasuffs_cache{$cat}{$form} = $result;
  return $result;
}

sub get_best_lemmasuffs {
  my $cat = shift;
  my $form = shift;
  my $token_pref = shift;
  if (defined($get_best_lemmasuffs_cache{$cat}{$form})) {
    return $get_best_lemmasuffs_cache{$cat}{$form};
  }
  $sth_cfslsc2->execute($cat,$form);
  my $result;
  while (my $value = $sth_cfslsc2->fetchrow) {
    $result = $token_pref.Encode::decode("utf8",$value);
    last;
  }
  $sth_cfslsc2->finish;
  $get_best_lemmasuffs_cache{$cat}{$form} = $result;
  return $result;
}
