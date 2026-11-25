class UnitJava < Formula
  desc "Java module for Unit application server"
  homepage "https://docs.freeunit.org"
  url "https://github.com/freeunitorg/freeunit.git",
      branch:   "1.37",
      revision: "56ab4a5baf518b501a1afabc6b1a8c7216805b91"
  version "1.37.3"

  head "https://github.com/freeunitorg/freeunit.git", branch: "master"

  livecheck do
    url "https://raw.githubusercontent.com/freeunitorg/freeunit/refs/heads/1.37/version"
    regex(/NXT_VERSION=(\S+)/i)
  end

  depends_on "openjdk@21"
  depends_on "openssl@3"
  depends_on "unit@1.37.3"

  def install
    system "./configure",
              "--prefix=#{prefix}",
              "--sbindir=#{bin}",
              "--logdir=#{var}/log",
              "--log=#{var}/log/unit/unit.log",
              "--runstatedir=#{var}/run",
              "--pid=#{var}/run/unit/unit.pid",
              "--control=unix:#{var}/run/unit/control.sock",
              "--modulesdir=#{HOMEBREW_PREFIX}/lib/unit/modules",
              "--statedir=#{var}/state/unit",
              "--tmpdir=/tmp",
              "--openssl",
              "--cc-opt=-I#{formula_opt_include("openssl")}",
              "--ld-opt=-L#{formula_opt_lib("openssl")}"

    inreplace "build/autoconf.data",
        "NXT_MODULESDIR='#{HOMEBREW_PREFIX}/lib/unit/modules'",
        "NXT_MODULESDIR='#{lib}/unit/modules'"

    inreplace "auto/modules/java",
         "$NXT_JAVAC -version 2>&1", "$NXT_JAVAC -version 2>/dev/null"

    system "./configure", "java"
    system "make", "java"
    system "make", "java-install"
  end

  test do
    require "socket"

    server = TCPServer.new(0)
    port = server.addr[1]
    server.close

    expected_output = "Hello world!"
    (testpath/"unit.conf").write <<~EOS
      {
        "listeners": { "*:#{port}": { "pass": "applications/test" } },
        "applications": {
          "test": { "type": "java", "webapp": "#{testpath}" }
        }
      }
    EOS
    (testpath/"index.jsp").write <<~EOS
      <%@ page contentType="text/plain"%>#{expected_output}
    EOS
    (testpath/"state/certs").mkpath

    system "#{HOMEBREW_PREFIX}/bin/unitd", "--log", "#{testpath}/unit.log",
                        "--control", "unix:#{testpath}/control.sock",
                        "--pid", "#{testpath}/unit.pid",
                        "--statedir", "#{testpath}/state"
    sleep 3

    pid = File.open(testpath/"unit.pid") { |f| f.gets.chop.to_i }

    system "curl", "-s", "--unix-socket", "#{testpath}/control.sock",
                    "-X", "PUT",
                    "-d", "@#{testpath}/unit.conf", "127.0.0.1/config"

    assert_match expected_output, shell_output("curl -s 127.0.0.1:#{port}")
  ensure
    Process.kill("TERM", pid)
  end
end
