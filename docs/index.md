# tarpitd.py

Slow your enemy down.

---

tarpitd.py is a **lightweight**, **single-file** network tarpit tool that deliberately delays or disrupts client connections by sending slow or malformed responses.

It implements a variety of response patterns that emulate common Internet services, intentionally disrupting client activities or even triggering crashes. This deceleration mechanism is particularly useful for **deterring malicious or misbehaving clients**, all while maintaining a low resource footprint. Start by reading the [introductory tutorial], then check the Unix-style [User Manual] for more information.

<style>
    body.homepage>div.container>div.row>div.col-md-3 {
    display: none;
}
</style>

[introductory tutorial]: getting-started.md
[User Manual]: manual/index.md

<div class="text-center">
<a href="getting-started/" class="btn btn-primary" role="button">Getting Started</a>
<a href="manual/" class="btn btn-primary" role="button">User Manual</a>
</div>

<div class="pt-2 pb-4 px-4 my-4 bg-body-tertiary rounded-3">
<h2 class="display-4 text-center">Features</h2>

<div class="row">
  <div class="col-sm-6">
    <div class="card mb-4">
      <div class="card-body">
        <h3 class="card-title">Lightweight</h3>
        <p class="card-text">
            The tool is purposefully designed as a single, streamlined file, ensuring a quick and easy download. 
            Not memory-intensive or CPU-intensive. Actually, it's "sleep-intensive".
        </p>
      </div>
    </div>
  </div>
  <div class="col-sm-6">
    <div class="card mb-4">
      <div class="card-body">
        <h3 class="card-title">Multi-protocol Support</h3>
        <p class="card-text">
            tarpitd.py isn’t limited to one communication standard: it is built with flexibility in mind. Whether the connection attempt uses SSH, HTTP, or even the robust standards of TLS, this tarpit is equipped to decelerating them all. 
        </p>
      </div>
    </div>
  </div>
</div>

<div class="row">
  <div class="col-sm-6">
    <div class="card">
      <div class="card-body">
        <h3 class="card-title">Structured Logging</h3>
        <p class="card-text">
            With its integration of the Python standard library’s logging module, tarpitd.py offers advanced logging capabilities. It captures detailed client connection data and outputs this information in a machine-friendly JSONL format
        </p>
      </div>
    </div>
  </div>
  <div class="col-sm-6">
    <div class="card">
      <div class="card-body">
        <h3 class="card-title">Client Verification</h3>
        <p class="card-text">
            A standout feature of tarpitd.py is its ability to check client before sending response. It ensures that each client receives the appropriate reply, and enable the ability to trick <a href="./about/#what-is-null-probing">null probing</a>.
      </div>
    </div>
  </div>
</div>
</div>
