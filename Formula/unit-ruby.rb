class UnitRuby < Formula
  desc "Ruby module for Unit application server"
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

  # The openssl formula of homebrew-core is the version 4. The whole stack
  # must use one OpenSSL version, so the paths point at the version 3.
  depends_on "openssl@3"
  depends_on "ruby"
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
              "--cc-opt=-I#{formula_opt_include("openssl@3")} -DNXT_HAVE_ISOLATION_ROOTFS=1",
              "--ld-opt=-L#{formula_opt_lib("openssl@3")}"

    inreplace "build/autoconf.data",
        "NXT_MODULESDIR='#{HOMEBREW_PREFIX}/lib/unit/modules'",
        "NXT_MODULESDIR='#{lib}/unit/modules'"

    # The module needs the ruby executable, not the directory of the binaries.
    system "./configure", "ruby", "--module=ruby",
        "--ruby=#{formula_opt_bin("ruby")}/ruby"
    system "make", "ruby-install"
  end

  def caveats
    <<~EOS
      Make sure rack gem installed:
        #{formula_opt_bin("ruby")}/gem install rack
    EOS
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
          "test": { "type": "ruby", "script": "#{testpath}/oper.ru" }
        }
      }
    EOS
    (testpath/"oper.ru").write <<~EOS
      app = Proc.new do |env|
          ['200', { 'Content-Type' => 'text/plain', }, ["#{expected_output}"]]
      end

      run app
    EOS
    (testpath/"state/certs").mkpath

    # The gem program of the ruby formula installs the rack gem.
    system formula_opt_bin("ruby")/"gem", "install", "rack"

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
    Process.kill("TERM", pid) if pid
  end
end
