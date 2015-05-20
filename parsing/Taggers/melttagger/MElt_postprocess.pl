#!/usr/bin/perl

binmode STDIN, ":utf8";
binmode STDOUT, ":utf8";
binmode STDERR, ":utf8";
use utf8;

$| = 1;

$remove_non_standard_amalgams = 0;
$tag_amalgam_with_its_last_component_tag = 0;
$keep_token_form_distinction = 0;
$lang = "fr";

while (1) {
    $_=shift;
    if (/^$/) {last;}
    elsif (/^-l(?:ang(?:age)?)?$/) {$lang=shift || die "Please provide a language code after -l option (en, fr)";}
    elsif (/^-npp$/) {$no_post_process = 1}
    elsif (/^-ktfd$/) {$keep_token_form_distinction = 1}
    elsif (/^-rnsa$/) {$remove_non_standard_amalgams = 1}
    elsif (/^-alct$/) {$tag_amalgam_with_its_last_component_tag = 1}
}

if ($lang eq "zzz" || $no_post_process) {
  while (<>) {
    s/^{([^}]+)} _XML\/[^ \n]+$/\1/;
    if (/{/ && $keep_token_form_distinction) {
      s/◁/\\{/g;
      s/▷/\\}/g;
      s/_ACC_O/\\{/g;
      s/_ACC_F/\\}/g;
    } else {
      s/{([^}]*)} *[^ ]+(\/[^ \/]+)/replace_whitespaces_with_underscores($1).$2/ge;
      s/◁/{/g;
      s/▷/}/g;
      s/_ACC_O/{/g;
      s/_ACC_F/}/g;
    }
    s/_UNDERSCORE/_/g;
    print $_;
  }
  exit 0;
}

while (<>) {
  chomp;
  s/^ +//;
  s/ +$//;
  $out = "";
  s/  +/ /g;

  # réalignement sur les tokens d'origine (premier pas)
  s/^\s*{(.*?)} *_XML\/[^ ]+\s*$/${1}/;
  if ($lang eq "en") {
    s/(^| )vs\.\/[^ ]+/$1vs\.\/IN/g;
    s/(^| )Vince\/[^ ]+/$1Vince\/NNP/g;
    s/(^| )Thanks\/[^ ]+/$1Thanks\/NNS/g;
    s/(^| )please\/[^ ]+/$1please\/UH/g;
    s/(^| )Please\/[^ ]+/$1Please\/UH/g;
    s/(^| )([AP]M)\/[^ ]+/$1$2\/NN/g;
    while (s/{([^{}]+) ([^{} ]+)} ([^ \/{}]+)\/([^ \/]+)/{$1} ${3}\/GW {$2} ${3}\/$4/g) {}
    s/(^| )>\/GW/\1>\/-RRB-/g;
    s/(^| )<\/GW/\1<\/-LRB-/g;
    s/({ *[^{} ]+ *})\s*_SMILEY\/[^ ]+/$1 _SMILEY\/NFP/g;
    s/({ *[^{} ]+ [^{}]+}\s*)_SMILEY\/[^ ]+/$1 _SMILEY\/NFP/g;
    s/_URL\/[^ ]+/_URL\/ADD/g;
    s/_EMAIL\/[^ ]+/_EMAIL\/ADD/g;
    s/_DATE[^ ]*\/[^ ]+/_EMAIL\/CD/g;
    s/_(?:TIME|HEURE)\/[^ ]+/_EMAIL\/CD/g;
    s/(^| )(l+o+l+|a+r+g+h+|a+h+a+|m+d+r+|p+t+d+r+)\/[^ ]+/$1$2\/NFP/gi; #|♥
    s/(^| )([•·\*o])\/[^ ]+/$1$2\/:/g; #?
    s/(^| )([^ {}]+\@[^ {}]{2,})\/[^ \/{}]+/\1\2\/ADD/g; # emails
    s/(^| )([^ {}]+\.{com,org,net,pdf,docx?})\/[^ \/{}]+/\1\2\/ADD/g; # files
    s/(^| )(http[^ {}]+\/[^ {}]+)\/[^ \/{}]+/\1\2\/ADD/g; # URLs
    s/(^| )(www\.[^ {}]+)\/[^ \/{}]+/\1\2\/ADD/g; # URLs
    s/(^| )([^ {}]+([=_\*-\~]{1,2})\3\3\3[^ {}]+)\/[^ \/{}]+/\1\2\/NFP/g;
    s/(^| )(\|)\/[^ \/{}]+/\1\2\/NFP/g;
    s/(^| )(s)\/[^ \/{}]+/\1\2\/AFX/g;
    s/^([A-Z][^ {}]+)\/[^ \/{}]+ ([^ {}]+\/ADD)/\1\/GW \2/g; # !!!
    s/^([A-Z][^ {}]+)\/[^ \/{}]+ ([A-Z])\/[^ \/{}]+ ([^ {}]+\/ADD)/\1\/GW \2\/GW \3/g; # !!!
    s/^-\/[^ {}]+ ([A-Z][^ {}]+)\/[^ \/{}]+ ([^ {}]+\/ADD)/-\/NFP \1\/GW \2/g; # !!!
    s/^-\/[^ {}]+ ([A-Z][^ {}]+)\/[^ \/{}]+ ([A-Z])\/[^ \/{}]+ ([^ {}]+\/ADD)/-\/NFP \1\/GW \2\/GW \3/g; # !!!
  } elsif ($lang eq "fr") {
    s/( je\/)[^ ]+/\1CLS/g;
    s/^((?:{[^{} ]+} )?)tu\/[^ ]+/\1tu\/CLS/g;
    s/( tu\/)[^ ]+ ((?:{[^{} ]+} )?[^ ]+\/VS?)/\1CLS \2/g;
    s/({ *[^{} ]+ *})\s*_SMILEY\/[^ ]+/$1 _SMILEY\/I/g;
    s/({ *[^{} ]+ [^{}]+})\s*_SMILEY\/[^ ]+/$1 _SMILEY\/X/g;
    s/^([0-9\.]+)\/[^ ]+$/\1\/META/;
    s/^([0-9\.]+)\/[^ ]+ \.\/[^ ]+$/\1\/META \.\/META/;
    s/({\#[^{} ]+}) _URL\/[^ ]+/\1 _URL\/KK/g;
    s/({[^\#][^{} ]*}) _URL\/[^ ]+/\1 _URL\/NPP/g;
#    s/_URL\/[^ ]+/_URL\/NPP/g;
    s/_EMAIL\/[^ ]+/_EMAIL\/NPP/g;
    s/(^| )(l+o+l+|a+r+g+h+|a+h+a+|♥)\/[^ ]+/$1$2\/I/gi;
    s/(^| )([•·\*o]|\.+)\/[^ ]+/$1$2\/PONCT/g;
    s/(^| )(Like|Share)\/[^ ]+/$1$2\/ET/g;
    s/(^|$)([^ ]+)\/[^ ]+ (at)\/[^ ]+ (\d+)\/[^ ]+ (:)\/[^ ]+ (\d+(?:[ap]m)?)\/[^ ]+/$1$2\/ADV $3\/P $4\/DET $5\/PONCT $6\/DET/g;
    s/(^|$)(\d+)\/[^ ]+ (people)\/[^ ]+ (like)\/[^ ]+ (this)\/[^ ]+/$1$2\/DET $3\/NC $4\/V $5\/PRO/g;
    s/(^|$)(\d+)\/[^ ]+ (hours|minutes|seconds)\/[^ ]+ (ago)\/[^ ]+/$1$2\/DET $3\/NC $4\/ADV/g;
    s/(^|$)(love)\/[^ ]+ (u|you)\/[^ ]+/$1$2\/V $3\/PRO/g;
    # pour smsalpes
    s/(^| )\*\/[^ ]+ \*\/[^ ]+ \*\/[^ ]+ ([A-Z]+)\/[^ ]+ (?:{_} _UNDERSCORE|_)\/[^ ]+ ([0-9]+)\/[^ ]+ \*\/[^ ]+ \*\/[^ ]+ \*\/[^ ]+( |$)/$1***$2_$3***\/NPP$4/g;
    s/(^| )\*\/[^ ]+ \*\/[^ ]+ \*\/[^ ]+ ([A-Z]+)\/[^ ]+ (?:{_} _UNDERSCORE|_)\/[^ ]+ ([0-9]+)\/[^ ]+ (?:{_} _UNDERSCORE|_)\/[^ ]+ ([0-9]+)\/[^ ]+ \*\/[^ ]+ \*\/[^ ]+ \*\/[^ ]+( |$)/$1***$2_$3_$4***\/NPP$5/g;
    s/(^| )\*\/[^ ]+ \*\/[^ ]+ \*\/[^ ]+ {([A-Z]+)} [^ ]+\/[^ ]+ (?:{_} _UNDERSCORE|_)\/[^ ]+ ([0-9]+)\/[^ ]+ \*\/[^ ]+ \*\/[^ ]+ \*\/[^ ]+( |$)/$1***$2_$3***\/NPP$4/g;
    s/(^| )\*\/[^ ]+ \*\/[^ ]+ \*\/[^ ]+ {([A-Z]+)} [^ ]+\/[^ ]+ (?:{_} _UNDERSCORE|_)\/[^ ]+ ([0-9]+)\/[^ ]+ (?:{_} _UNDERSCORE|_)\/[^ ]+ ([0-9]+)\/[^ ]+ \*\/[^ ]+ \*\/[^ ]+ \*\/[^ ]+( |$)/$1***$2_$3_$4***\/NPP$5/g;
  }

  s/}_/} _/g;

  $out = "";

  # réalignement sur les tokens d'origine
  while ($_ ne "") {
    if (s/^{([^ {}]+)} ([^ {}]+(?: \{\} *[^ {}]+)+)( |$)//) {
      $t = $1;
      $f = $2;
      $f =~ s/^[^ ]*\///;
      $f =~ s/ {} [^ ]*\//+/g;
      $t =~ s/^(.*)◀.*/\1/;
      if ($f =~ /\+/) {
	if ($remove_non_standard_amalgams && $f ne "P+D" && $f ne "P+PRO") {
	  $f = "X";
	} elsif ($tag_amalgam_with_its_last_component_tag) {
	  $f =~ s/^.*\+//;
	}
      }
      $out .= " $t/$f";
    } elsif (s/^{([^ {}]+(?: [^{}]+)+)} ([^ {}]+)\/([^ {}\/]+)( |$)//) {
      $t = $1;
      $f = $2;
      $tag = $3;
      $t =~ s/^(.*)◀.*/\1/;
      if ($remove_non_standard_amalgams) {
	$t =~ s/ /\/Y /g;
	$out .= " $t/Y";
      } else {
	if ($lang eq "fr") {
	  $t =~ s/ /\/Y /g;
	} else {
	  $t =~ s/ /\/GW /g;
	}
	$out .= " $t/$tag";
      }
    } elsif (s/^{([^ {}]+)} ([^ {}]+)( |$)//) {
      $t = $1;
      $f = $2;
      $t =~ s/^(.*)◀.*/\1/;
      $f =~ s/^.*\///;
      $out .= " $t/$f";
    } elsif (s/^([^{} ]+)( |$)//) {
      $out .= " $1";
    } else {
      die $_;
    }
    s/^ *//;
  }
  $out =~ s/◁/{/g;
  $out =~ s/▷/}/g;
  $out =~ s/^ +//;
  $out =~ s/ +$//;
  print $out."\n";
}

sub replace_whitespaces_with_underscores {
  my $s = shift;
  $s =~ s/ /_/g;
  return $s;
}
