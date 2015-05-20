#!/usr/bin/env perl
# $Id: segmenteur.pl 5184 2013-05-04 18:23:11Z magistry $


# Principe général
# ----------------

# On procède en deux temps
# 1. tokenisation (on insère ou supprime des blancs:
#    à l'issue, un blanc est une frontière de tokens)
#    Ceci n'est pas fait si -no_sw
# 2. segmentation (les tokens constitués de points ou 
#    d'autres ponctuations sont susceptibles d'être des 
#    frontières de phrases
# L'option -no_s permet de ne faire que la partie 1 
# (les frontières de phrases restent de simples blancs)

# Spécificités:
# - on utilise le fichier passé en paramètres (-af=xxx) 
#   pour ne pas traiter comme un cas normal les points 
#   terminant des abréviations connues
# - on essaye d'être fin sur les points frontières de 
#   phrases et les autres
# - on essaye de ne pas mettre de frontière de phrase 
#   au milieu d'une citation bien balancée
# - l'option -p=[rp] permet de privilégier le rappel 
#   (les phrases peuvent sans problème commencer par 
#   une minuscule) ou la précision (les phrases ne 
#   commencent pas par une minuscule)
# - l'encodage de l'input est lue dans le fichier 
#   encoding du dossier du lexique correspondant
#   à la langue (à défaut, utf8)

use utf8;
use Encode;



$| = 1;

$lang = "fr";
$toksent=1;
$no_af=0;
$no_sw=-1;
$cut_on_apos=0;
$cut_on_hyphen=0;
$sent_bound="\n";
$qsent_bound="_SENT_BOUND";
$print_par_bound = 0;
$weak_sbound = 1;
$affixes = 0; # car normalement géré par text2dag
#$split_before_ne=0;
my $best_recall=0;

my %dict;
my $has_dict = 0;
my $alexinadir = "/usr/local/share/alexina"; # valeur par défaut

binmode STDIN, ":utf8";
binmode STDERR, ":utf8";
binmode STDOUT, ":utf8";

while (1) {
    $_=shift;
    if (/^$/) {last;}
    elsif (/^-s$/ || /^-split-sentences?$/i) {$toksent=1;}
    elsif (/^-no_s$/ || /^-no_split[_-]sentences?$/i) {$toksent=0;}
    elsif (/^-sb$/ || /^-sentences?-boundary$/i) {$sent_bound=shift;} elsif (/^-sb=(.*)$/ || /^-sentences?-boundary=(.*)$/i) {$sent_bound=$1;}
    elsif (/^-qsb$/ || /^-quotes?-sentences?-boundary$/i) {$qsent_bound=shift;} elsif (/^-qsb=(.*)$/ || /^-quotes?-sentences?-boundary=(.*)$/i) {$qsent_bound=$1;}
    elsif (/^-no_qsb$/ || /^-no[_-]quotes?-sentences?-boundary$/i) {$qsent_bound="";}
    elsif (/^-af$/ || /^-abbrev-file$/i) {$abrfilename=shift;} elsif (/^-af=(.*)$/ || /^-abbrev-file=(.*)$/i) {$abrfilename=$1;}
    elsif (/^-no_af$/ || /^-no_abbrev-file$/i) {$no_af=1; $abrfilename=""}
    elsif (/^-sw$/ || /^-no_split-words$/i) {$no_sw=0;}
    elsif (/^-no_sw$/ || /^-no_split-words$/i) {$no_sw=1;}
    elsif (/^-ca$/ || /^-cut_on_apos$/i) {$cut_on_apos=1;}
    elsif (/^-ch$/ || /^-cut_on_hypen$/i) {$cut_on_hyphen=1;}
    elsif (/^-a$/ || /^-affixes$/i) {$affixes=1;}
    elsif (/^-r$/ || /^-p=r$/ || /^-best_sbound_recall$/i) {$initialclass=$l; $best_recall=1} # on segmente bcp
    elsif (/^-n$/ || /^-p=p$/ || /^-best_sbound_precision$/i) {$initialclass=$maj;} # on segmente normalement
    elsif (/^-p$/) {$initialclass=$maj; $weak_sbound = 0} # on segmente moins
    elsif (/^-ppb$/ || /^-print_par_bound$/i) {$print_par_bound = 1;}
    elsif (/^-kbl$/ || /^-keep_blank_lines$/i) {$keep_blank_lines = 1;}
    elsif (/^-alexinadir$/) {$alexinadir = shift;} elsif (/^-alexinadir=(.*)$/) {$alexinadir = $1;}
    elsif (/^-l$/ || /^-lang$/i) {$lang=shift;} elsif (/^-l=(.*)$/ || /^-lang=(.*)$/i) {$lang=$1;}
}

if ($lang =~ /^(fr|en|it|es|pt|sv|no|de)/) {
  $min=qr/(?:[a-zæœàåâäãéêèëîïøöôùûüÿçóúíáòì])/;
  $maj=qr/(?:[A-ZÀÅÃÉÈÊËÂÄÔÖÛÜÇÓÚÍÁÒØÌÆŒ])/;
  $l=qr/(?:[æœàåâäãéêèëîïöôùûüÿçøóúíáòìa-zA-ZÀÅÃÉÈÊËÂÄÔÖÛÜÇÓÚÍÁÒØÌÆŒ])/;
  $nonl=qr/(?:[^a-zæœàåâäãéêèëîïöøôùûüÿçóúíáòìA-ZÀÅÃÉÈÊËÂÄÔÖÛÜÇÓÚÍÁÒØÌÆŒ])/;
} elsif ($lang =~ /^(pl|cz|sk|ro|sl|hr|sr|sc|bn|tr|fa|ckb)$/) {
  $min=qr/(?:[a-záäąćčďéęěëíĺľłńňóôöŕřśšťúůüýźż])/;
  $maj=qr/(?:[A-ZÁÄĄĆČĎÉĘĚËÍĹŁĽŃŇÓÔÖŔŘŚŠŤÚŮÜÝŹŻ])/;
  $l=qr/(?:[a-záäąćčďéęěëíĺľłńňóôöŕřśšťúůüýźżA-ZÁÄĄĆČĎÉĘĚËÍĹŁĽŃŇÓÔÖŔŘŚŠŤÚŮÜÝŹŻ ])/;
  $nonl=qr/(?:[^a-záäąćčďéęěëíĺľłńňóôöŕřśšťúůüýźżA-ZÁÄĄĆČĎÉĘĚËÍĹŁĽŃŇÓÔÖŔŘŚŠŤÚŮÜÝŹŻ ])/;
} elsif ($lang =~ /^(ru|uk|bg|bl|kk)$/) {
  $min=qr/(?:[a-zабвгдежзийклмнопрстуфхцчшщэюяыьё])/;
  $maj=qr/(?:[A-ZАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯЫЬЁ])/;
  $l=qr/(?:[a-zабвгдежзийклмнопрстуфхцчшщэюяыьёA-ZАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯЫЬЁ ])/;
  $nonl=qr/(?:[^a-zабвгдежзийклмнопрстуфхцчшщэюяыьёA-ZАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯЫЬЁ ])/;
} elsif ($lang =~ /^(gr)$/) {
  $min=qr/(?:[a-zα-ωάέήίόύώϊϋΐΰ])/;
  $maj=qr/(?:[A-ZΑ-ΩΆΈΉΊΌΎΏΪΫ])/;
  $l=qr/(?:[a-zA-Zα-ωάέήίόύώϊϋΐΰΑ-ΩΆΈΉΊΌΎΏΪΫ ])/;
  $nonl=qr/(?:[^a-zA-Zα-ωάέήίόύώϊϋΐΰΑ-ΩΆΈΉΊΌΎΏΪΫ ])/;
} else {
  $min=qr/(?:[a-zæœáäąãćčďéęěëíĺľłńňóôöŕřśšťúůüýźżàåâäãéêèëîïøöôùûüÿçóúíáòì])/;
  $maj=qr/(?:[A-ZÁÄĄÃĆČĎÉĘĚËÍĹŁĽŃŇÓÔÖŔŘŚŠŤÚŮÜÝŹŻÀÅÃÉÈÊËÂÄÔÖÛÜÇÓÚÍÁÒØÌÆŒ])/;
  $l=qr/(?:[a-zæœáäąãćčďéęěëíĺľłńňóôöŕřśšťúůüýźżàåâäãéêèëîïøöôùûüÿçóúíáòìA-ZÆŒÁÄĄÃĆČĎÉĘĚËÍĹŁĽŃŇÓÔÖŔŘŚŠŤÚŮÜÝŹŻÀÅÃÉÈÊËÂÄÔÖÛÜÇÓÚÍÁÒØÌ ])/;
  $nonl=qr/(?:[^a-zæœáäąãćčďéęěëíĺľłńňóôöŕřśšťúůüýźżàåâäãéêèëîïøöôùûüÿçóúíáòìA-ZÆŒÁÄĄÃĆČĎÉĘĚËÍĹŁĽŃŇÓÔÖŔŘŚŠŤÚŮÜÝŹŻÀÅÃÉÈÊËÂÄÔÖÛÜÇÓÚÍÁÒØÌ ])/;
}
$initialclass=$maj;


# if ($lang ne "" && $u8seg != 1 && -r "$alexinadir/$lang/encoding" && open ENCODING, "<$alexinadir/$lang/encoding") {
#   $encoding = <ENCODING>;
#   chomp($encoding);
#   if ($encoding =~ /^(?:(?:iso)?-?8859-|l(?:atin)?-?)-?(\d+)$/i) {
#     binmode STDIN, ":encoding(iso-8859-$1)";
#     binmode STDOUT, ":encoding(iso-8859-$1)";
#   }
#   close ENCODING;
# }

if ($lang =~ /^(zh|tw)$/) {
  for (</usr/local/share/alexina/$lang/*.lex>) {
    open DICT, "<$_" || next;
    binmode DICT, ":utf8";
    while (<DICT>) {
      chomp;
      s/^#.*//;
      /^(.)(.*?)\t/ || next;
      $tmpdict{$1}{$2} = 1;
      $has_dict = 1;
    }
    close DICT;
  }
  for $firstchar (keys %tmpdict) {
    @{$dict{$firstchar}} = sort {length($b)<=>length($a)} keys %{$tmpdict{$firstchar}};
  }
}

if ($no_sw == -1) {
  $no_sw = 0;
#  if ($lang =~ /^(ja|tw|zh|th|ko)$/) {
  if ($lang =~ /^(ja|th|ko)$/) {
    $no_sw = 1;
  }
}

if ($lang =~ /^(fa|ckb)$/) {$weak_sbound = 2}

$sent_bound =~ s/\\n/\n/g;
$sent_bound =~ s/\\r/\r/g;
$sent_bound =~ s/\\t/\t/g;
$sent_bound =~ s/^"(.*)"$/\1/;
$qsent_bound =~ s/\\n/\n/g;
$qsent_bound =~ s/\\r/\r/g;
$qsent_bound =~ s/\\t/\t/g;
$qsent_bound =~ s/^"(.*)"$/\1/;

$qsent_bound =~ s/\\n/\n/g;
$qsent_bound =~ s/\\r/\r/g;
$qsent_bound =~ s/\\t/\t/g;
$qsent_bound =~ s/^"(.*)"$/\1/;

my $cut_on_apos_re = "";
if ($cut_on_apos) {
  if ($lang eq "fr") {
    $cut_on_apos_re = join('|', qw/c m n j s t aujourd d l qu puisqu lorsqu quelqu presqu prud quoiqu jusqu/);
    $cut_on_apos_re = qr/(?:$cut_on_apos_re)/i;
  }
}

@abr=();
@abrp=();
my $temp;
my $temp2;
if ($abrfilename=~/\w/) {
  if (open (ABR,"<$abrfilename")) {
    while (<ABR>) {
      if ((/^\"..+\"$/ || /^[^\"].+$/) && /^[^\#]/) {
	chomp;
	s/_/ /g;
	s/^(.*[^\.].*\.)\.$/$1\_FINABR/; # peuvent être des abréviations finissant par point et finissant une phrase (type etc.)
	s/^\"//;
	s/\"$//;
	$rhs = $_;
	$rhs_nospace = $rhs;
	$rhs_nospace=~s/_FINABR//;
	$rhs_nospace=~s/ //g;
	$rhs_nospace2rhs{$rhs_nospace}=$rhs;
	s/([\.\[\]\(\)\*\+])/\\$1/g; # échappement des caractères spéciaux
	s/^\\\. */\\\. \*/g;
	s/(?<=.)\\\. */ \*\\\. \*/g;
	if (s/ \*_FINABR$//) {
	  push(@abr_fin,$rhs);
	  push(@abrp_fin,$_);
	} else {
	  s/ \*$//;
	  push(@abr,$rhs);
	  push(@abrp,$_);
	}
      }
    }
    close (ABR);
    $abrp_re = join("|",sort {length($b) <=> length($a)} @abrp);
    $abrp_re = qr/($abrp_re)/o;
    $abrp_fin_re = join("|",sort {length($b) <=> length($a)} @abrp_fin);
    $abrp_fin_re = qr/($abrp_fin_re)/o;
  } else {
    print STDERR "The dot-including abbreviation file $abrfilename could not be opened ($!). Ignoring such abbreviations.\n";
    $no_af = 1;
  }
} elsif (!$no_af) {
  print STDERR "No dot-including abbreviation file given\n";
  $no_af = 1;
}

$par_bound = -1;

while (<STDIN>) {
    chomp;
    if (/ (_XML|_MS_ANNOTATION) *$/) {
	print "$_\n";
	$par_bound = 0;
	next;
    } elsif ($par_bound == -1) {
      $par_bound = 0;
    } else {
      $par_bound = 1;
    }

    if ($par_bound && $print_par_bound) {
      print " _PAR_BOUND\n";
    }

    s/  *{/{ /g;
    s/(} *[^ ]+) * / \1 /g;
    s/ +  +/   /g;

    s/^/ /; s/$/ /;
    if (!$no_sw) {
      if ($lang !~ /^(ja|zh|tw|th)/) {                               # si on peut tokeniser soi-même...
	s/(?<=[^\.\t])\.+(\s\s+)/ \.$1/g; # si suivi de deux blancs (ou TABs) ou plus, point+ est un token
	s/(?<=\t)\.+(\s\s+)/\.$1/g;	  # idem
	s/ +/ /g;      # ceci étant exploité, on normalise les espaces
	s/\t+/\t/g;
	s/ +\t/\t/g; s/\t +/\t/g;

	s/(_(?:UNSPLIT|REGLUE|SPECWORD)_[^\s{]+)/\1_PROTECT_/g; # on protège de la segmentation des tokens déjà découpés et identifiés par _UNSPLIT_ ou _REGLUE_
	s/({[^{}]+} *$l+)\+($l*)/\1__PLUS__\2/g;
	if ($lang =~ /^(fr|es|it)$/) {
	  s/[ \(\[]\'([^ \'][^\']*?[^ \'])\'(?=[ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])/ ' \1 ' /g; # les apostrophes peuvent servir à quoter...
	  s/  / /g;
	  if ($lang eq "it") {
	    s/ e\'(?=[ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])/ {e'} è/g;
	    s/(?<=[ \/\\:;\"“”\+-])([A-Za]?[a-z]+(?:[ielsrtn]t|[eirdavtp]r|ci|al|ap|of|ol|ag))a\'(?=[ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])/{$1a'} $1à/g;
	    s/(?<=[ \/\\:;\"“”\+-])([A-Za]?[a-z]+(?:pi|n[dt]|bl|iv|u[ld]|gi|ab))u\'(?=[ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])/{$1u'} $1ù/g;
	    s/(?<=[ \/\\:;\"“”\+-])([A-Za]?[a-z]+(?:[eubfvpgmsdczlntir]))o\'(?=[ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])/{$1o'} $1ò/g;
	  }
	  unless ($lang eq "it") {
	    s/(?<=[^\'\s_])\'\s*/\'/g; # par défaut, on supprime les blancs suivant les guillemets sauf après " '" et "''", sauf en italien (redondant avec ci-dessus, mais sécurité... ou ci-dessus à supprimer (ou supprimer d'ici... à voir))
	  }
	  s/(?<=\s)\'(?=[^ _])/$1\' /g; # en français, espagnol et italien, les autres guillemets sont détachés
	} elsif ($lang eq "en") {
	  s/([a-z])\'([a-z])/\1__APOS__\2/g;
#	  s/[ \(\[]'([^ '][^']*?[^ '])'(?=[ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])/ ' \1 ' /g; # les apostrophes peuvent servir à quoter...
	  $lq = s/(?<=[ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])(['`])(?=[^ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])/\1/g;
	  $rq_no_s = s/(?<=[^ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.Ss])'(?=[ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])/'/g;
	  $sq = s/(?<=[Ss])\'(?=[ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])/'/g;
	  if ($sq == 0 && $lq == 0 && $rq_no_s == 0) {
	  } elsif ($sq == 0 && $lq == $rq_no_s) {
	    s/(?<=[ \(\[])([\'\`])([^ \'](?:[^\'])*?[^ \'sS])\'(?=[ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])/ {\1} ` \2 ' /g; # les apostrophes peuvent servir à quoter...
	  } elsif ($sq == 1 && $lq == $rq_no_s) {
	    s/(?<=[ \(\[])(['\`])([^ '](?:[^']|[sS]')*?[^ 'sS])'(?=[ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])/ {\1} ` \2 ' /g; # les apostrophes peuvent servir à quoter...
	  } else {
	    $_ = reverse($_);
	    s/(?<=[ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])'([^ '](?:[^']|'[sS])*?[^ '])(['\`])(?=[ \(\[])/ ' \1 ` \}\2\{ /g; # les apostrophes peuvent servir à quoter...
	    $_ = reverse($_);
	    s/{`} ` /` /g;
	  }
	  s/__APOS__/'/g;
	  s/  / /g;
	} elsif ($lang !~ /^(ckb|fa)/) {
	  s/[ \(\[]'([^ '][^']*?[^ '])'(?=[ ,;?\!:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\˝\&\`\.])/ ' \1 ' /g; # les apostrophes peuvent servir à quoter...
	  s/  / /g;
	}
	while (s/({[^}]*) ([^}]*}\s*_(?:EMAIL|SMILEY|EPSILON|URL|META_TEXTUAL_PONCT|SENT_BOUND|ETR|SPECWORD|TMP_[^ ]+))/$1\_SPACE$2/g) {
	} # on protège les espaces déjà présents dans ces entités nommées (cf ci dessous)
	if ($lang !~ /^(?:fr|en|es|it|nl|de|pt)$/) {
	  while (s/}( *[^}]*) *(&[^; ]+;|[,;?\!¿¡:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\&])([^ ]+) _(UNSPLIT|REGLUE)/}$1 _$4_$2_PROTECT_ _$4_$3 _$4/g) {}
	  s/ *(&[^; ]+;|[,;?\!¿¡:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\&]) */ $1 /g; # on isole toutes les ponctuations (et assimilées) sauf le point
	  if ($lang !~ /^(?:fa|ckb)$/) {
	    s/ *([\`\˝]) */ $1 /g; # on isole toutes les ponctuations (et assimilées)  (˝ est un double accent aigu (hongrois) utilisé parfois comme guillement en l2)
	  } else {
	    s/ *([\.]+) */ $1 /g; # on isole toutes les ponctuations (et assimilées)
	    s/ *( ) */ $1 /g; # on isole toutes les ponctuations (et assimilées)
	  }
	} else {
	  while (s/}( *[^}]*) *(&[^; ]+;|[,;?\!\¿\¡:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\&\`])([^ _]+) _(UNSPLIT|REGLUE)/}$1 _$4_$2_PROTECT_ _$4_$3 _$4/g) {}
	  s/ *(&[^; ]+;|[,;?\!\¿\¡:\"“”\)\(\*\#<>\[\]\%\/\\\=\+\«\»\&\`]) */ $1 /g; # on isole toutes les ponctuations (et assimilées) sauf le point
	  if ($lang eq "fr") {
	    s/(^| )«  /\1«_NBSP /g; # on attache les espaces insécables à leur ponctuation associée, en les protégeant à cause de l'opération ci-dessous
	    s/  ([»;:]|[\?\!]+)( |$)/ _NBSP\1\2/g;
	    s/ *  */   /g; # les espaces insécables restants sont considérés comme des tokens en soi
	    s/_NBSP/ /g; # on rétablit les espaces insécables associés à des ponctuations
	  }
	}
	s/ +([^ ]+) +_PROTECT_/$1_PROTECT_/g;
	s/__PLUS__/+/g;
	s/  +/ /g;
	s/ &quot; / {&quot;} " /g;
	s/ &apos;/ {&apos;} '/g;
	s/ *(_UNDERSCORE|_ACC_O|_ACC_F) */ $1 /g; # on isole aussi les ponctuations échappées
	while (s/({[^}]*) ([^}]*}\s*_(?:META_TEXTUAL_PONCT|SENT_BOUND|ETR|SPECWORD|TMP_[^ ]+))/$1$2/g) {
	}	# les espaces qu'on vient d'insérer sont mauvais dans 
	# ces entités nommées: on les enlève...
	s/_SPACE/ /g;	  # ...et on restaure ceux qui y étaient avant
	s/_PROTECT_//g;
	s/} +_UNSPLIT_/} /g;

	if ($lang eq "fr") {
	  s/($nonl)et\s*\/\s*ou($nonl)/$1 et\/ou $2/g; # cas particulier: cas particulier pour et/ou
	} elsif ($lang eq "en") {
	  s/($nonl)and\s*\/\s*or($nonl)/$1 and\/or $2/g; # cas particulier: cas particulier pour and/or
	}
	s/\&\s*(amp|quot|lt|gt)\s*;/\&$1;/g; # cas particulier: entités XML
	s/ &lt; -/&lt;-/g;	# cas particulier: flèches
	s/- &gt; /-&gt; /g;	# cas particulier: flèches

	s/ +\t/\t/g; s/\t +/\t/g;
	s/(\.\.*) +/$1 /g; s/(\.\.*) *$/$1 /g; # un seul blanc derrière 2 points ou plus

	# les entnom sont des tokens
	s/\} *(_[A-Za-z_]+)/"} $1".space_unless_is_SPECWORD($1)/ge;
	s/ _(UNSPLIT|REGLUE)_ / _$1_/g;

	# POINT après une minuscule
	while (s/(} [^ ]+$min)(\.\.*\s*)([\(\[\"“”\)\]\?\!¿¡\'\/\\\_\˝][^{}]*|(?:$l)[^{}]*)?(\{|$)/$1 _UNSPLIT_$2 $3$4/g) {} # avant certaines poncts ou une lettre ou retour-chariot ou {, point+ est un token, mais pas dans les commentaires... !!! cas particulier où on détache la ponct d'un truc qui a déjà un commentaire (expérimental) - peut arriver si on a mis -no_sw sur gl_number.pl mais pas sur segmenteur.pl, par exemple
	while (s/($min)(\.\.*\s*)([\(\[\"“”\)\]\?\!¿¡\'\/\\\_\˝][^{}]*|(?:$l)[^{}]*)?(\{|$)/$1 $2 $3$4/g) {} # avant certaines poncts ou une lettre ou retour-chariot ou {, point+ est un token, mais pas dans les commentaires...
	s/($min)(\.\.+\s*)([^ ])/$1 $2 $3/g; # avant qqch d'autre (y compris un chiffre), il faut 2 points pour cela
	s/(\d)\. /\1 . /g; # ceci dit, chiffre-point-blanc fait du point une ponct (attention, un tel chiffre est dans un bouzin style H1N1 ou G8, sinon il serait _NUM)
	s/($maj)\. *$/\1 . /; # ... et en fin de ligne, le point final est une ponct (risqué, cf une phrase se finissant par S.N.C.F.)
	s/($maj$maj)\. ($maj)/\1 . \2/g; # pire, les séquences $maj$maj. $maj font du point une ponct (très risqué)
	s/ +\t/\t/g; s/\t +/\t/g;

	# POINT après une majuscule
	s/\b($maj\.)($maj$min)/$1 $2/g; # insertion d'un blanc entre maj-point et maj-min
	s/($maj{3,})\./$1 \./g;	# 3 majuscules de suite puis point -> le point est une ponct
	s/\.($maj{3,})/\. $1/g;	# point puis 3 majuscules de suite -> le point est une ponct

	# POINT après un chiffre
	s/(\d)(\.+)([^0-9])/$1 $2 $3/g; # chiffre point non-chiffre -> le point est une ponct
	
	# TIRETS et slashes
	s/(\d)(\s*\-\s*)(\d)/$1 $2 $3/g; # le tiret entre 2 chiffres est une ponct
	s/([\(\[\"“”\)\]\,\;\%\˝])\-/$1 -/g; # le tiret après une ponct autre que point en est séparé
	s/\-([\(\[\"“”\)\]\,\;\%\˝])/- $1/g; # le tiret avant une ponct autre que point en est séparé
	s/($l)([\/\\\-])\s*($l)/$1$2$3/g;	# recollages de tirets ou de slashes
	s/($l)\s*([\/\\\-])($l)/$1$2$3/g;
	s/ +\t/\t/g; s/\t +/\t/g;

	s/ *$//g;
	s/\n/\#\n/g; # on marque d'un "#" les fins de ligne dans le texte brut

	# toilettage final
	s/ +\t/\t/g; s/\t +/\t/g;
	# BS: lignes suivantes douteuses
	#	s/\. +([\-\{])/ . $1/g;
	#	s/([^\{])\{/$1 \{/g;

	if ($lang =~ /^(fr|es|it)$/) {
	  s/(\s)\'(?=[^ _])/$1\' /g; # rebelotte, car des nouveaux blancs ont pu être insérés
	}
	if ($cut_on_hyphen) {
	  s/([^ ])-([^ ])/\1 _-_ \2/g;
	  s/([^ _])-([^ _])/\1 _-_ \2/g;
	  s/([^ ])-( (?:,|{))/\1 _-_\2/g;
	  if ($lang eq "fr") {
	    s/([^ ]t) _-_ (ils?|elles?|on) /$1 {_-_ $2} -$2 /g;
	  }
	}
	if ($cut_on_apos && $cut_on_apos_re ne "") {
	  while (s/ (${cut_on_apos_re})'([^ ])/ \1' \2/g) {}
	}
	s/(\s[\/\\\.])($l)/$1 $2/g; # changé pour les tirets
	s/^ *([\/\\\.])($l)/$1 $2/g; # changé pour les tirets
	s/(\s\.)-/$1 -/g;
	s/\.(-\s)/. $1/g;
	#    } elsif (a$lang eq "ja") {
	#      print STDERR ">$lang: $_\n";
	#      $_ = join ("/",TinySegmenter->segment($_));
      } elsif ($lang =~ /^(tw|zh)$/ && $has_dict) {
	s/(?<=[^\s])([\"“”\*\%\«\»\˝]\s)/ _REGLUE_$1/g; # prudence
	s/(\s[\"“”\*\%\«\»\˝])([^\s]+)/$1 _REGLUE_$2/g; # prudence
	s/(?<=_REGLUE_)\s+_REGLUE_//g;
	s/(?<=_UNSPLIT_)\s+_REGLUE_//g;
	my $tokenized = "";
	my $unparsed = "";
	while (s/^(.)//) {
	  $firstchar = $1;
	  $did_something = 0;
	  if (defined($dict{$firstchar})) {
	    for $n (0..$#{$dict{$firstchar}}) {
	      $otherchars = $dict{$firstchar}[$n];
	      $otherchars = quotemeta($otherchars);
	      if (s/^$otherchars//) {
		if ($unparsed ne "") {$tokenized .= $unparsed." "}
		$tokenized .= $firstchar.$otherchars." ";
		$unparsed = "";
		$did_something = 1;
		last;
	      }
	    }
	  }
	  if ($did_something == 0) {
	    $unparsed .= $firstchar;
	  }
	}
	if ($unparsed ne "") {$tokenized .= $unparsed." "}
	$_ = $tokenized;
	s/{ +/{/g;
	s/ +}/}/g;
	s/ ^//;
      } elsif ($lang =~ /^(zh|tw)/) {
	while (s/({[^}]*) /${1}_SPACE/g) {}
	s/([\p{Han}])/ $1 /go;
	if ($lang =~ /^zh-/){
		s/([\p{Thai}])/ $1 /go;
	}
	s/([-。…，！：、？?「」『』…（）“”":,\.!'《》();；【】«»\"\*\+＋＝=－－——－／\/\\℃])(\1*)/ $1$2 /g;
	s/  +/ /go;
	while (s/({[^}]*) /$1/g) {}
	s/_SPACE/ /g;
      } else {
	s/(?<=[^\s])([\"“”\*\%\«\»\˝]\s)/ _REGLUE_$1/g; # prudence
	s/(\s[\"“”\*\%\«\»\˝])([^\s]+)/$1 _REGLUE_$2/g; # prudence
	s/(?<=_REGLUE_)\s+_REGLUE_//g;
	s/(?<=_UNSPLIT_)\s+_REGLUE_//g;
      }
    } else {
#      print STDERR "$lang: $_\n";
	s/(?<=[^\s])([\"“”\*\%\«\»\˝]\s)/ _REGLUE_$1/g; # prudence
	s/(\s[\"“”\*\%\«\»\˝])([^\s]+)/$1 _REGLUE_$2/g; # prudence
	s/(?<=_REGLUE_)\s+_REGLUE_//g;
	s/(?<=_UNSPLIT_)\s+_REGLUE_//g;
    }
    s/^/  /;
    s/$/  /;

    # Recollages particuliers
    s/(?<=[^\}]) (R \& [Dd]) / {$1} R\&D /go;
    if ($lang eq "fr") {      # ATTENTION : blanc non convertis en \s
      s/(?<=[^\}]) (C ?\. N ?\. R ?\. S ?\.) / {$1} C.N.R.S. /go;
      s/(?<=[^\}]) (S ?\. A ?\. R ?\. L ?\.) / {$1} S.A.R.L. /go;
      s/(?<=[^\}]) (S ?\. A ?\.) / {$1} S.A. /go;
      s/(?<=[^\}]) M +\. / {M .} M. /go;
      s/(?<=[^\}]) ([tT][eéEÉ][Ll]) +\. / {\1 .} \1. /go;
      s/(?<=[^\}]) \+ \+ / {+ +} ++ /go;
      s/(?<=[^\}]) \+ \/ \- / {+ \/ -} +\/- /go;
    }
    s/(?<=[^\}]) Mr +\. / {Mr .} Mr. /go;
    s/(?<=[^\}]) (autocad) / {$1} _SPECWORD_AutoCAD /gi;

    if ($lang eq "en") {
      if ($expand_contractions) {
	s/(?<=[^\}]) ([aA])in't / {\1in't} \1re _UNSPLIT_not /goi;      
	s/(?<=[^\}]) ([cC]a)n't / {\1n't} \1n _UNSPLIT_not /goi;      
	s/(?<=[^\}]) ([Ww])on't / {\1on't} \1ill _UNSPLIT_not /goi;      
	s/(?<=[^\}]) ([^ _][^ ]*)n't / {\1n't} \1 _UNSPLIT_not /goi;      
	s/(?<=[^\}]) ([Ii])'m / {\1'm} I _UNSPLIT_am /goi;      
	s/(?<=[^\}]) ([Yy]ou|[Ww]e)'re / {\1're} \1 _UNSPLIT_are /goi;      
	s/(?<=[^\}]) (I|you|we|they|should|would)'(ve) / {\1've} \1 _UNSPLIT_have /goi;      
	s/(?<=[^\}]) (I|you|he|she|we|they|there)'(d) / {\1'd} \1 _UNSPLIT_would /goi;      
	s/(?<=[^\}]) (I|you|he|she|we|they|there)'(ll) / {\1'll} \1 _UNSPLIT_will /goi;      
	s/(?<=[^\}]) (they)'(re) / {\1're} \1 _UNSPLIT_are /goi;
	s/(?<=[^\}]) ([^ ]*[^ s_])'s / {\1's} \1 _UNSPLIT_'s /goi;
	s/(?<=[^\}]) ([^ _][^ ]*s)'(?!s |\}.)/ {\1'} \1 _UNSPLIT_'s /goi;
      } elsif (0) {
	s/(?<=[^\}]) ([aA])in't / {\1in't} \1re _UNSPLIT_n't /goi;      
	s/(?<=[^\}]) ([cC]a)n't / {\1n't} \1n _UNSPLIT_n't /goi;      
	s/(?<=[^\}]) ([Ww])on't / {\1on't} \1ill _UNSPLIT_n't /goi;
	s/(?<=[^\}]) ([^ ]+)n't / {\1n't} \1 _UNSPLIT_n't /goi;      
	s/(?<=[^\}]) ([Ii])'m / {\1'm} I _UNSPLIT_'m /goi;      
	s/(?<=[^\}]) ([Yy]ou|[Ww]e)'re / {\1're} \1 _UNSPLIT_'re /goi;      
	s/(?<=[^\}]) (I|you|we|they|should|would)'(ve) / {\1've} \1 _UNSPLIT_'ve /goi;      
	s/(?<=[^\}]) (I|you|he|she|we|they|there)'(d) / {\1'd} \1 _UNSPLIT_'d /goi;      
	s/(?<=[^\}]) (I|you|he|she|we|they|there)'(ll) / {\1'll} \1 _UNSPLIT_'ll /goi;      
	s/(?<=[^\}]) (they)'(re) / {\1're} \1 _UNSPLIT_'re /goi;
	s/(?<=[^\}]) ([^ ]*[^ s])'s / {\1's} \1 _UNSPLIT_'s /goi;
	s/(?<=[^\}]) ([^ ]*s)'(?!s |\}.)/ {\1'} \1 _UNSPLIT_'s /goi;
      } else {
	s/(?<=[^\}]) ([aA])in't / {\1in't} \1re _UNSPLIT_n't /goi;      
	s/(?<=[^\}]) ([cC]a)n't / {\1n't} \1n _UNSPLIT_n't /goi;      
	s/(?<=[^\}]) ([Ww])on't / {\1on't} \1ill _UNSPLIT_n't /goi;
	s/(?<=[^\}]) ([^_ ][^ ])n't / {\1n't} \1 _UNSPLIT_n't /goi;      
	s/(?<=[^\}]) ([Ii])'m / {\1} I 'm /goi;      
	s/(?<=[^\}]) ([Yy]ou|[Ww]e)'re / \1 're /goi;      
	s/(?<=[^\}]) (I|you|we|they|should|would)'(ve) / \1 '\2 /goi;      
	s/(?<=[^\}]) (I|you|he|she|we|they|there)'(d|ll) / \1 '\2 /goi;      
	s/(?<=[^\}]) (they)'(re) / \1 '\2 /goi;
	s/(?<=[^\}]) ([^ ]*[^ s_])'s / \1 's /goi;
	s/(?<=[^\}]) ([^ _][^ ]*s)'(?!s |\}.)/ \1 {'} 's /goi;
      }
    } elsif ($lang eq "fr") {
      s/(?<=[^\}]) ([Ss]) ' (\S+)/ {\1 '} \1' \2/goi;
      s/(?<=[^\}]) (\') / {$1} " /go;
      s/ ([ldnmst]) ([aeéiouy]\S+)/ {\1} \1' \2/goi;
    }

    s/(?<=[^\}]) \'([^ ]+)\' / {'\1'} ' \1 ' /goi;

    if (!$no_sw) {
      if ($lang eq "fr") {
	# hyphenated suffixes
	# doit-elle => doit -elle
	# ira-t-elle => ira -t-elle
	# ira - t -elle => ira => -t-elle
	s/(- ?t ?)?-(ce|elles?|ils?|en|on|je|la|les?|leur|lui|[mt]oi|[vn]ous|tu|y)(?![-a-zA-Z0-9éèêîôûëïüäù])/ $1-$2/go ;
	# donne-m'en => donne -m'en
	s/(- ?t ?)?-([mlt]\')/ $1-$2/go ;
	s/-(née?s?|cl(?:é|ef)s?|ci|là)(?![-a-zA-Z0-9éèêîôûëïüäù])/ _-$1/go ;
	# hyphenated prefixes
	while (s/(?<=[^\}]) ((?:qu|lorsqu|puisqu|quelqu|quoiqu|[dlnmtcjs])\')(?=[^ ])/ \1 /goi) {}
	if ($affixes) {
	  # ATTENTION:  normalement, ce travail est fait plus tard, par text2dag. Ceci ne devrait être utilisé que si l'on utilise sxpipe comme tokenizer pur (i.e., sans faire de vraie différence entre token et forme)
	  if ($lang eq "fr") {
	    # hyphenated suffixes
	    
	    # hyphenated prefixes
	    # anti-bush => anti- bush
	    # franco-canadien => franco- canadien
	    s/((?:anti|non|o|ex|pro)-)/$1 /igo ;
	  }
	}
      }
    }

    s/(?<=[^\}])(\s+)(\( \.\.\. \))(\s+)/$1\{$2} (...)$3/go;
    s/(?<=[^\}])(\s+)(\[ \.\.\. \])(\s+)/$1\{$2} (...)$3/go;
    s/(?<=[^\}])(\s+)(\! \?)(\s+)/$1\{$2} !?$3/go;
    s/(?<=[^\}])(\s+)(\? \!)(\s+)/$1\{$2} ?!$3/go;
    s/(?<=[^\}])(\s+)(\!(?: \!)+)(\s+)/$1\{$2} !!!$3/go;
    s/(?<=[^\}])(\s+)(\?(?: \?)+)(\s+)/$1\{$2} ???$3/go;
    s/(?<=[^\}])(\s+)(\^\s+\^\s+)([^ \{\}]+)/$1\{$2$3\} $3 /go;
    s/(?<=[^\}]) ([^ \{\}\(\[]+) \^ ([^ \{\}]+)/{$1 ^ $2} $1\^$2/go;
    s/^\s+([^\s\{\}\(\[]+)(\s\^\s)([^\s\{\}]+)/\{$1$2$3\} $1\^$2/go;
    s/((?:_UNDERSCORE\s?)+_UNDERSCORE)([^_]|$)/ {$1} _UNDERSCORE $2/go;
    s/((?:_ACC_O\s?)+_ACC_O)(\s|$)/ {$1} _ACC_O$2/go;
    s/((?:_ACC_F\s?)+_ACC_F)(\s|$)/ {$1} _ACC_F$2/go;
    
    s/(?<=[^\}]) (turn over) / {$1} turn-over /g;
    s/(?<=[^\}]) (check liste?) / {$1} check-list /g;
      s/(?<=[^\}]) (i-?phone)(s?) / {$1$2} iPhone$2 /gi;
      s/(?<=[^\}]) (i-?pad)(s?) / {$1$2} iPad$2 /gi;
      s/(?<=[^\}]) (i-?mac)(s?) / {$1$2} iMac$2 /gi;
    if ($lang eq "fr") {
      #abréviations courantes
      s/(?<=[^\}])([- ])([Qq])qfois /$1\{$2qfois} $2elquefois /go;
      s/(?<=[^\}])([- ])([Ee])xple /$1\{$2xple} $2xemple /go;
      s/(?<=[^\}])([- ])([Bb])cp /$1\{$2cp} $2eaucoup /go;
      s/(?<=[^\}])([- ])([Dd])s /$1\{$2s} $2ans /go;
      s/(?<=[^\}])([- ])([Mm])(gm?t) /$1\{$2$3} $2anagement /go;
      s/(?<=[^\}])([- ])([Nn])s /$1\{$2s} $2ous /go;
      s/(?<=[^\}])([- ])([Nn])b /$1\{$2b} $2ombre /go;
      s/(?<=[^\}])([- ])([Tt])ps /$1\{$2ps} $2emps /go;
      s/(?<=[^\}])([- ])([Tt])(jr?s) /$1\{$2$3} $2oujours /go;
      s/(?<=[^\}])([- ])([Qq])que(s?) /$1\{$2ue$3} $2uelque$3 /go;
      s/(?<=[^\}])([- ])([Qq])n /$1\{$2n} $2uelqu'un /go;
      s/(?<=[^\}])([- ])([Cc])(\.?-?[aà]\.?-?d\.?) /$1\{$2$3} $2'est-à-dire /go;
      s/(?<=[^\}])([- ])([Nn])breu(x|ses?) /$1\{$2breu$3} $2ombreu$3 /go;
      s/(?<=[^\}])([- ])([^ ]+t)([º°]) /$1\{$2$3} $2ion(s) /go;
      s/(?<=[^\}])([- ])([Ss])(nt) /$1\{$2$3} $2ont /go;
      s/(?<=[^\}])([- ])(le|du|les|ce) ([wW][Ee]) /$1$2 \{$3} week-end /go;
      
      # fautes courantes
      s/(?<=[^\}]) (avant gardiste) / {$1} avant-gardiste /g;
      s/(?<=[^\}])([- ])à (fortiori|priori|posteriori|contrario) /$1\{à} a $2 /go;
      s/(?<=[^\}])([- ])pa /$1\{pa} pas /go;
      s/(?<=[^\}])([- ])er /$1\{er} et /go;
      s/(?<=[^\}])([- ])([Qq])uant ([^aà])/$1\{$2uant} $2and $3/go;
      s/(?<=[^\}])([- ])QUANT ([^AÀ])/$1\{QUANT} QUAND $2/go;
      s/(?<=[^\}])([- ])([Cc]) (est|était) /$1\{$2} $2' $3 /go;
      s/(?<=[^\}])([- ])(Etats[- ][Uu]nis) /$1\{$2} États-Unis /go;
      s/(?<=[^\}])([- ])([Rr])([eé]num[eé]ration) /$1\{$2$3} $2émunération /go;
      s/(?<=[^\}])([- ])c (est|ets) /$1\{c} c' \{$2} est /go;
    } elsif ($lang eq "en") {
      #abréviations courantes
      s/(?<=[^\}])([- ])(acct(?: ?\.)?) /$1\{$2} account /g;
      s/(?<=[^\}])([- ])(addl(?: ?\.)?) /$1\{$2} additional /g;
      s/(?<=[^\}])([- ])(amt(?: ?\.)?) /$1\{$2} amount /g;
      s/(?<=[^\}])([- ])(approx(?: ?\.)?) /$1\{$2} approximately /g;
      s/(?<=[^\}])([- ])(assoc(?: ?\.)?) /$1\{$2} associate /g;
      s/(?<=[^\}])([- ])(avg(?: ?\.)?) /$1\{$2} average /g;
      s/(?<=[^\}])([- ])(bldg(?: ?\.)?) /$1\{$2} building /g;
      s/(?<=[^\}])([- ])(incl(?: ?\.)?) /$1\{$2} including /g;
      s/(?<=[^\}])([- ])(intl(?: ?\.)?) /$1\{$2} international /g;
      #s/(?<=[^\}])([- ])(jan(?: ?\.)?) /$1\{$2} January /g;
      #s/(?<=[^\}])([- ])(feb(?: ?\.)?) /$1\{$2} February /g;
      #s/(?<=[^\}])([- ])(apr(?: ?\.)?) /$1\{$2} April /g;
      #s/(?<=[^\}])([- ])(aug(?: ?\.)?) /$1\{$2} august /g;
      #s/(?<=[^\}])([- ])(sep(?: ?\.)?) /$1\{$2} September /g;
      #s/(?<=[^\}])([- ])(oct(?: ?\.)?) /$1\{$2} October /g;
      #s/(?<=[^\}])([- ])(nov(?: ?\.)?) /$1\{$2} November /g;
      #s/(?<=[^\}])([- ])(dec(?: ?\.)?) /$1\{$2} December /g;
      s/(?<=[^\}])([- ])(max(?: ?\.)?) /$1\{$2} maximum /g;
      s/(?<=[^\}])([- ])(mfg(?: ?\.)?) /$1\{$2} manufacturing /g;
      s/(?<=[^\}])([- ])(mgr(?: ?\.)?) /$1\{$2} manager /g;
      s/(?<=[^\}])([- ])(mgt(?: ?\.)?) /$1\{$2} management  /g;
      s/(?<=[^\}])([- ])(mgmt(?: ?\.)?) /$1\{$2} management /g;
      s/(?<=[^\}])([- ])(std(?: ?\.)?) /$1\{$2} standard /g;
      s/(?<=[^\}])([- ])(w \/ o) /$1\{$2} without /g;
      s/(?<=[^\}])([- ])(dept(?: ?\.)?) /$1\{$2} department /g;
      s/(?<=[^\}])([- ])(wk(?: ?\.)?) /$1\{$2} week /g;
      s/(?<=[^\}])([- ])(div(?: ?\.)?) /$1\{$2} division /g;
      s/(?<=[^\}])([- ])(asst(?: ?\.)?) /$1\{$2} assistant /g;
      s/(?<=[^\}])([- ])(av(?: ?\.)?) /$1\{$2} average /g;
      s/(?<=[^\}])([- ])(avg(?: ?\.)?) /$1\{$2} average /g;
      s/(?<=[^\}])([- ])(co(?: ?\.)?) /$1\{$2} company /g;
      s/(?<=[^\}])([- ])(hr(?: ?\.)?) /$1\{$2} hour /g;
      s/(?<=[^\}])([- ])(hrs(?: ?\.)?) /$1\{$2} hours /g;
      s/(?<=[^\}])([- ])(mo(?: ?\.)?) /$1\{$2} month /g;
      #s/(?<=[^\}])([- ])(mon(?: ?\.)?) /$1\{$2} Monday /g;
      #s/(?<=[^\}])([- ])(tue(?: ?\.)?) /$1\{$2} Tuesday /g;
      #s/(?<=[^\}])([- ])(wed(?: ?\.)?) /$1\{$2} Wednesday /g;
      #s/(?<=[^\}])([- ])(thu(?: ?\.)?) /$1\{$2} Thursday /g;
      #s/(?<=[^\}])([- ])(fri(?: ?\.)?) /$1\{$2} Friday /g;
      #s/(?<=[^\}])([- ])(sun(?: ?\.)?) /$1\{$2} Sunday /g;
      s/(?<=[^\}])([- ])(no ?\.) /$1\{$2} number /g;
      s/(?<=[^\}])([- ])(yr(?: ?\.)?) /$1\{$2} year /g;
      s/(?<=[^\}])([- ])(abt) /$1\{$2} about /g;
      s/(?<=[^\}])([- ])(jr(?: ?\.)?) /$1\{$2} junior /g;
      s/(?<=[^\}])([- ])(jnr(?: ?\.)?) /$1\{$2} junior /g;
      s/(?<=[^\}])([- ])(mo(?: ?\.)?) /$1\{$2} month /g;
      s/(?<=[^\}])([- ])(mos(?: ?\.)?) /$1\{$2} months /g;
      s/(?<=[^\}])([- ])(sr(?: ?\.)?) /$1\{$2} senior /g;
      s/(?<=[^\}])([- ])(co-op) /$1\{$2} cooperative  /g;
      s/(?<=[^\}])([- ])(co(?: ?\.)?) /$1\{$2} company /g;
      s/(?<=[^\}])([- ])(cond(?: ?\.)?) /$1\{$2} condition  /g;
      s/(?<=[^\}])([- ])(corp(?: ?\.)?) /$1\{$2} corporation  /g;
      s/(?<=[^\}])([- ])(dba(?: ?\.)?) /$1\{$2} doing _UNSPLIT_business _UNSPLIT_as /g;
      s/(?<=[^\}])([- ])(dbl(?: ?\.)?) /$1\{$2} double /g;
      s/(?<=[^\}])([- ])(ea(?: ?\.)?) /$1\{$2} each  /g;
      s/(?<=[^\}])([- ])(inc(?: ?\.)?) /$1\{$2} incorporated /g;
      s/(?<=[^\}])([- ])(int'l) /$1\{$2} international /g;
      s/(?<=[^\}])([- ])(ltd) /$1\{$2} limited  /g;
      #s/(?<=[^\}])([- ])(m-f(?: ?\.)?) /$1\{$2} Monday _UNSPLIT_through _UNSPLIT_Friday  /g;
      s/(?<=[^\}])([- ])(misc(?: ?\.)?) /$1\{$2} miscellaneous  /g;
      s/(?<=[^\}])([- ])(msg(?: ?\.)?) /$1\{$2} message  /g;
      #s/(?<=[^\}])([- ])(spd(?: ?\.)?) /$1\{$2} Speed /g;
      s/(?<=[^\}])([- ])(w(?: ?\. ?)?r(?: ?\. ?)?t(?: ?\.)?) /$1\{$2} with _UNSPLIT_respect _UNSPLIT_to /g;
      s/(?<=[^\}])([- ])(e(?: ?\. ?)?g(?: ?\.)?) /$1\{$2} e.g. /g;
      s/(?<=[^\}])([- ])(i(?: ?\. ?)?e(?: ?\.)?) /$1\{$2} i.e. /g;
      s/(?<=[^\}])([- ])(ibid(?: ?\.)?) /$1\{$2} ibidem /g;
      s/(?<=[^\}])([- ])(pb(?: ?\.)?) /$1\{$2} problem /g;

      # fautes courantes
      s/(?<=[^\}])([- ])(today)(s) /$1\{$2$3} $2 _UNSPLIT_'$3 /goi;

      s/(?<=[^\}]) (i) / \{$1} I /go;

      s/(?<=[^\}])([- ])([Rr])(enum[ea]ration) /$1\{$2$3} $2muneration /go;
      s/(?<=[^\}])([- ])([Aa]t)(le?ast|most|all) /$1\{$2$3} $2 _UNSPLIT_$3 /go;
      s/(?<=[^\}])([- ])(wright) /$1\{$2} right /go;
      s/(?<=[^\}])([- ])(Wright) /$1\{$2} Right /go;
      s/(?<=[^\}])([- ])(Objectie)(s?) /$1\{$2$3} Objective$3 /go;
      s/(?<=[^\}])([- ])(do) (note) /$1 $2 \{$3} ___not /go;
      s/ ___not (,|that|the|a) / note $1 /go;
      s/ ___not / not /go;
    } elsif ($lang eq "fa") {
      s/(?<=[^\}]) ([^ ]+)_ra / {\1_ra} \1 _UNSPLIT_ra /g;
      s/(?<=[^\}]) ([^ ]+[aw])([_ ])y([ymtš]) / {\1\2y\3} \1y\3 /g;
      s/(?<=[^\}]) ([^ ]+[ey])([_ ])a([ymtš]) / {\1\2a\3} \1a\3 /g;
      s/(?<=[^\}]) ([^ ]+[^ay])([_ ])([ymtš]) / {\1\2\3} \1\3 /g;
      s/(?<=[^\}]) ([^ ]+[aw])([_ ])y([mtš]an) / {\1\2y\3} \1y\3 /g;
      s/(?<=[^\}]) ([^ ]+[^a])([_ ])([mtš]an) / {\1\2\3} \1\3 /g;
      s/(?<=[^\}]) ([^ ]+) (ea) / {\1 \2} \1_\2 /g;
      s/(?<=[^\}]) ([^ ]+) (eay[mtš]) / {\1 \2} \1_\2 /g;
      s/(?<=[^\}]) ([^ ]+) (eay[mtš]an) / {\1 \2} \1_\2 /g;
      s/(?<=[^\}]) (n?my) ([^ {]+) / {\1 \2} \1_\2 /g;
      s/(?<=[^\}]) na ([^ {]+) / {na \1} na_\1 /g;
    }

    # re-collage des points appartenant à des abréviations
    if ($no_af != 1) {
      if ($lang =~ /^(fr|en|kmr|it|de|es|nl|pt)$/) {
	s/(?<=[^a-zàâäéêèëîïöôùûüÿçA-ZÀÉÈÊËÂÄÔÖÛÜÇ\_\-])$abrp_re(\s+[^\s])/{$1} get_normalized_pctabr($1).$2/ge;
	s/(?<=[^a-zàâäéêèëîïöôùûüÿçA-ZÀÉÈÊËÂÄÔÖÛÜÇ\_\-])$abrp_fin_re(\s|$)/{$1} get_normalized_pctabr($1).$2/ge;
      } elsif ($lang !~ /^(ru|uk|bg)$/) {
	s/(?<=[^a-zабвгдежзийклмнопрстуфхцчшщэюяыьёA-ZАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯЫЬЁ\_\-\s])$abrp_re(\s+[^\s])/{$1} get_normalized_pctabr($1).$2/ge;
	s/(?<=[^a-zабвгдежзийклмнопрстуфхцчшщэюяыьёA-ZАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯЫЬЁ\_\-\s])$abrp_fin_re(\s|$)/{$1} get_normalized_pctabr($1).$2/ge;
      } elsif ($lang !~ /^(ja|zh|tw|th)$/) {
	s/(?<=[^a-záäąćčďéęěëíĺľłńňóôöŕřśšťúůüýźżA-ZÁÄĄĆČĎÉĘĚËÍĹŁĽŃŇÓÔÖŔŘŚŠŤÚŮÜÝŹŻ\_\-\s])$abrp_re(\s+[^\s])/{$1} get_normalized_pctabr($1).$2/ge;
	s/(?<=[^a-záäąćčďéęěëíĺľłńňóôöŕřśšťúůüýźżA-ZÁÄĄĆČĎÉĘĚËÍĹŁĽŃŇÓÔÖŔŘŚŠŤÚŮÜÝŹŻ\_\-\s])$abrp_fin_re(\s|$)/{$1} get_normalized_pctabr($1).$2/ge;
      }
    }

    if ($lang !~ /^(ja|zh|tw|th)$/) {
      # abréviations en point qui sont en fin de phrase
      # _UNSPLIT_ a pour effet que les tokens (dans les commentaires) associés
      # à la ponctuation finale seront les mêmes que ceux associés à la forme précédente,
      # i.e. à l'abréviation:
      # echo "adj." | sxpipe    donne:
      # {<F id="E1F1">adj</F> <F id="E1F2">.</F>} adj. {<F id="E1F1">adj</F> <F id="E1F2">.</F>} .
      # c'est tok2cc/rebuild_easy_tags.pl qui fait ce travail
      # on ne le fait que si l'abréviation concernée a le droit de terminer une phrase,
      # ce qui est indiqué dans le lexique par le fait qu'elle se termine par 2 points (!)
      s/(?<=[^\.\s\_])(\.\_FINABR\.*) *$/\. _UNSPLIT_$1/;

      # Il faut maintenant gérer les abrév reconnues dans une entnom (type "{{godz .} godz. 16} _TIME")
      if ($no_sw) {
	while (s/(\{[^\{\}]*)\{([^\{\}]*)\} [^ ]+/$1$2/g) {
	}
      } else {
	while (s/(\{[^\{\}]*)\{[^\{\}]*\} ([^ ]+)/$1$2/g) {
	}
      }
      s/  */ /g;
      s/^ //;
    }

    # Détachements particuliers
    if ($lang eq "pl") {
      if ($no_sw) {
	s/(^|\s)(przeze|na|za|do|ode|dla|we)(ń)(\s|$)/$1\{$2$3\} $2 \{$2$3\} _$3$4/g;
      } else {
	s/(^|\s)(przeze|na|za|do|ode|dla|we)(ń)(\s|$)/$1$2 \{$3\} _$3$4/g;
      }
    }

    # SEGMENTATION en phrases si pas d'option -no_s
    # ---------------------------------------------
    # on identifie de toute façon les frontières de phrases
    # - si -no_s, on les indique par un espace
    # - sinon, on en a de 2 types: 
    #     * celles repérées par #__# sont remplacées par un retour-chariot,
    #     * celles reprérées par #_# sont remplacées par $sent_bound, 
    #       qui vaut retour-chariot par défaut mais qui peut être redéfini 
    #       par -sb=XXX (souvent, XXX = _SENT_BOUND)

    while (s/({[^}]*) ([^}]*}\s*_(?:EMAIL|SMILEY|EPSILON|URL|META_TEXTUAL_PONCT|SENT_BOUND|ETR|SPECWORD|TMP_[^ ]+))/$1\_SPACE$2/g) {
    } # on protège ces entités nommées pour y éviter des tokenisations abusives induites par la segmentation (cf plus bas)

    s/ +\t/\t/g; s/\t +/\t/g;
    s/  +/ /g;
    s/\t\t+/\t/g;

    if ($lang =~ /^(ja|zh|tw)$/) {
      s/ ([！？\!\?。｡]|) / \1 \#__\#/g;
      if ($weak_sbound > 0) {
	s/ ([：；:;]|) / \1 \#_\#/g;
      }
    } elsif ($lang !~ /^(ja|zh|tw|th)$/) {
      s/([\.:;\?\!])\s*([\"“”\˝]\s*(?:$maj|[\[_\{])[^\"“”\˝]*[\.:;\?\!]\s*[\"“”\˝])\s*(\s$maj|[\[\{]|$)/$1\#\_\#$2\#\_\#$3/g; # détection de phrases entières entre dbl-quotes
      s/(?<=\s)(\.\s*_UNDERSCORE)/{$1} ./go; # ad hoc pour mondediplo et ses underscores de fin d'article (?)
      #    $special_split = ($split_before_ne) ? qr/[\{\[_]/ : qr/[\[_]/;
      $special_split = qr/[\{\[_¿¡]/;
      if (!$no_sw) {
	s/(?<=[^\.])(\.\.*)\s*(\(\.\.\.\))\s($maj|[\[_\{\.])/ $1\#\_\#$2\#\_\#$3/g;
	s/([^\.][0-9\}\s]\.\.*)\s*($initialclass|$special_split)/$1\#\_\#$2/g; # CAS STANDARD
	s/($l|[\!\?])(\s*\.\.\.)\s($l|$special_split)/$1$2\#\_\#$3/g;
	s/(\.\s+\.\.*)\s*($maj|$special_split)/$1\#\_\#$2/g;
	s/\_FINABR\s*($initialclass|$special_split)/ _UNSPLIT_.\#\_\#$1/g;
      } else {
	s/(?<=\s)(\.\.*)(\s+\[\.\.\.\])(\s+$maj|[\[_\{\.])/$1\#\_\#$2\#\_\#$3/g;
	s/([^\.]\s+\.\.*)(\s+$initialclass|$special_split)/$1\#\_\#$2/g; # CAS STANDARD
	s/($l|[\!\?])(\s*\.\.\.*)(\s+(?:$l|$special_split))/$1$2\#\_\#$3/g;
	s/\_FINABR(\s*$initialclass|$special_split)/ _UNSPLIT_.\#\_\#$1/g;
      }
      s/(\.\s*\.+)(\s+$initialclass|[\[_\{\-\«¿¡])/$1\#\_\#$2/g;	 # attention !!!
      s/([\?\!]\s*\.*)(\s+$initialclass|[\[_\{\-\«¿¡])/$1\#\_\#$2/g; # attention !!!
      s/([\.\?\!]\s*\.\.+)(\s+)/$1\#\_\#$2/g;			   # attention
      s/([\.\?\!,:])(\s+[\-\+\«¿¡])/$1\#\_\#$2/g;			   # attention
      if ($weak_sbound > 0) { # si $weak_sbound, on segmente sur les deux-points
	s/(:\s*\.*)(\s+$initialclass|[\[_\{\-\«¿¡])/$1\#\_\#$2/g; # attention !!!
	s/(:\s*\.\.+)(\s+)/$1\#\_\#$2/g;			# attention
      }
    }

    s/(?<!TA_TEXTUAL_PONCT|_META_TEXTUAL_GN)(\s+\{[^\}]*\} _META_TEXTUAL)/\#\_\#$1/g;	# attention

    if ($lang !~ /^(ja|zh|tw|th)$/) {    
      if ($best_recall) {
	s/(,)(\s+[\-\+])/$1\#\_\#$2/g; # attention
      }
      while (s/^((?:[^\"“”]*[\"“”\˝][^\"“”]*[\"“”\˝])*[^\"“”]*[\.;\?\!])(\s+[\"“”\˝])/$1\#\_\#$2/g) {}											 # attention
      while (s/^([^\"“”]*[\"“”\˝](?:[^\"“”]*[\"“”\˝][^\"“”]*\"“”)*[^\"“”]*[\.;\?\!]\s+[\"“”\˝])\s+/$1\#\_\#/g) {}				# attention

      if ($weak_sbound > 0) {
	s/(\s+);(\s+)/$1;\#\_\#$2/g; # les points-virgules sont des frontières de phrases ($sent_bound à la sortie, qui peut être retour chariot)
	s/;#_# ([\"“”\˝])#_#/; $1#_#/g;
	if ($weak_sbound == 2) {
	  s/(\s+)\.(\s+)/$1 \.\#\_\#$2/g; # cas des langues sans majuscules..
	}
      }
    }

    s/$/\#\__\#/; # tout retour chariot dans le source est une frontière de paragraphe (retour chariot à la sortie)

    while (s/({[^}]*)(?: |#_+#)([^}]*}\s*_(?:EMAIL|SMILEY|EPSILON|URL|META_TEXTUAL_PONCT|SENT_BOUND|ETR|SPECWORD|TMP_[^ ]+))/$1$2/g) {
    }

    if ($toksent) {			    # si on nous demande de segmenter en phrases
      if ($lang !~ /^(ja|zh|tw|th)$/) {    
	# si on a détecté une frontière de phrase, tout point+ qui la précède est à isoler
	if (!$no_sw) {
	  s/([^\.\{_])(\.+\s*)\#\_\#/$1 $2\#_\#/g;
	} else {
	  s/(\s\.+)\s*\#\_\#/$1\#_\#/g;
	  s/([^\.\s\{_])(\.+)\s*\#\_\#/$1 _REGLUE_$2\#_\#/g;
	}
      }
      while (s/(\{[^\}]*)\#\_\#/$1 /g) {
      }

      # attention: ces lignes ne gèrent (pour l'instant) pas les profondeurs
      #   de parenthèses supérieures à 1. Si donc on a "( ( ) #_# )", c'est un peu la cata
      if ($lang =~ /^(fa|ckb|ar|he)$/) { # langues qui écrivent les trucs de droite à gauche, et qui donc ont des ouvrantes et fermantes "inversées"
	while (s/(\)[^\(]*)\#\_\#/$1 /g) {
	}		       
      } else {
	while (s/(\([^\)]*)\#\_\#/$1 /g) {
	}		       
      }

      s/#_+#\s*_(UNSPLIT|REGLUE)/ _$1__SENT_BOUND _$1/g;

      # on essaye de ne pas couper dans les citations
      my @array = split /(?=[\"“”])/, " $_ ";
      $_ = "";
      for my $i (0..$#array) {
	if ($array[$i] =~ s/^([\"“”])//) {$_ .= $1}
	if ($i % 2 == 1) {
	  $array[$i] =~ s/#_#/ $qsent_bound /g;
	} else {
	  $array[$i] =~ s/^#_#,/ $qsent_bound ,/g;
	  $array[$i] =~ s/:#_#$/: $qsent_bound /g;
	}
	$_ .= "$array[$i]";
      }
      s/\s*\#\_\#\s*/ $sent_bound /g;
      s/\s*\#\__\#\s*/\n/g;
    } else {
      s/\#\_+\#/ /g;
      s/$/\n/;
    }
    s/\_FINABR//g;
    s/ +/ /g;
    s/(^|\n) +/\1/g;
    s/ +$//;

    s/_SPACE/ /g;	  # on restaure ceux qui étaient à l'origine dans les entités nommées

    if (/( - .*){8,}/) { # à partir de 8 (choisi au plus juste), on va considérer qu'on est face à une liste
      s/ - /\n- /g;
    }

    # sortie
    if ($_!~/^ *$/) { # && $_!~/^-----*$/ && $_!~/^\d+MD\d+$/) {
      if (!$no_sw) {
	s/(\S){/\1 {/g;
      }        
      print "$_";
    } elsif ($keep_blank_lines && /^\s*$/) {
      print "\n";
    }
}

sub get_normalized_pctabr {
  my $s = shift;
  $s =~ s/\s+//g;
  return $rhs_nospace2rhs{$s};
}

sub space_unless_is_SPECWORD {
  my $s = shift;
  if ($s =~ /^_SPECWORD/) {return ""}
  return " ";
}
