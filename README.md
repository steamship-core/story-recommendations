# Async Prompt Chain Runner [Experiment] 

This package implements an asynchronous prompt chain runner.
It manages storage and execution of chains in the cloud.

* **Chains** are provided as JSON templates of arbitrary length.
* **Invocations** run chains on user input
  * Invocations run asynchronously in the cloud
  * Callbacks are supported when each step and the full chain finishes
  * Errors that occur mid-chain are propagated to the end
* **Generative Models** can be invoked via [Steamship Plugins](https://steamship.com/plugins)
  * `gpt-3` - via [https://steamship.com/plugins/gpt-3](https://steamship.com/plugins/gpt-3)
  * `dall-e` - Coming Soon
  
## Full Documentation

### Creating a Chain Runner

You can create a Chain Runner

* **On the web** by clicking [https://steamship.com/packages/async-prompt-chain-experiment](https://steamship.com/packages/async-prompt-chain-experiment), click on the **My Private Instances** tab and then **Create Instance**
* **In Python**, by running
  ```python
  from steamship import Steamship
  runner = Steamship.use('async-prompt-chain-experiment', 'my-unique-id')
  ```
* **In Typescript**, by runing
  ```typescript
  import {Steamship} from '@steamship/client'
  const runner = await Steamship.use('async-prompt-chain-experiment', 'my-unique-id')  
  ````

### Creating a Chain

Create a new chain using a simple declarative syntax (see below).
Then, invoke the `create_chain` method.

**Python:**

```python
# See below for a full example of a chain_dict
runner.invoke('create_chain', chain=chain_dict)
```

**Typescript:**

```typescript
// See below for a full example of a chain_obj
await runner.invoke('create_chain', {chain: chain_obj})
```

That will return a dict object of the form:

```json
{ "chain_id": "uuid" }
```

### Invoking a Chain

Invoke a chain by passing it input arguments.

**Python:**

```python
input_arguments = {"arg1": "arg1"}
runner.invoke('run_chain', chain_id=chain_id, inputs=input_arguments, callback_url="https://..")
```

**Typescript:**

```typescript
await runner.invoke('run_chain', {
    chain_id: "chain_id", 
    inputs: {
        arg1: "argw"
    },
    callback_url: "url"
})
```

That will return a dict object of the form:

```json
{
  "input": {},
  "output": "string",
  "state": "succeeded | failed | running | waiting",
  "statusMessage": "if error occurs",
  "steps": [
    {
      "state": "succeeded | failed | running | waiting",
      "statusMessage": ".. step-level information"
    }
  ]
}
```

## Chain Definition Language

This API uses a simple declarative language to define chains.

### Chain Object

The chain object is defined as:

```
{
  steps: Step[]
  callback_url?: string
}
```

### Step Object
The step object is defined as:

```
{
    handle: string,   # Required. For naming the output and debugging.
    prompt: string,   # Prompt to pass to the model 
    input:  {},       # Optional; hard-coded values to interpolate into the promp, overwriting user input and chain input.
    plugin: str       # The Generator (text, image, audio) Steamship plugin to apply
    plugin_config: {} # The configuration of the plugin
}
```

### Valid Plugins

The `plugin` field may be:

* `gpt-3` - Requires a configuration of `{"max_words": int}`

### Chain Execution

Each step in the chain receives an input variable object containing: 

* The input the user provided to invocation.
* Plus: The output from all Steps 0..Prior. The key in the dictionary is the `handle` on the step
* Plus: Any `input` dict provided in the current step's configuration.

Interpolation is done against the prompt using Python's string formatting semantics.

## Complete Example

Below is an extremely simple prompt demonstrating a simple prompt chain.

* Calling `create_chain` would return a `chain_id` that represents this chain.
* Calling `run_chain`, the user could provide the arguments `{topic: "food"}` and receive back a judgement
  on whether a generated joke is funny.
  * The intermediate step output is also returned.

1. First, put this in prompt_chain.json

```json
{
  "handle": "single-prompt",
  "steps": [
    {
      "handle": "tell-joke",
      "plugin": "gpt-3",
      "plugin_config": { "max_words":  10 },
      "prompt": "Tell me a joke about {topic}"
    },
    {
      "handle": "judge-joke",
      "plugin": "gpt-3",
      "plugin_config": { "max_words":  10 },
      "prompt": "A comedian told a joke:\n\n{tell-joke}\n\n Is it funny? YES/NO:"
    }
  ]
}
```

2. Second, put this in `client.js`

```javascript
async function main() {
  if (!process.env.STEAMSHIP_API_KEY) {
    console.log("Please visit https://steamship.com/account/api to get an api key. Then set the STEAMSHIP_API_KEY environment variable")
    return;
  }
  // This gives us a new instance of the API
  const Steamship = (await import('@steamship/client')).Steamship;
  const runner = await Steamship.use('async-prompt-chain-experiment', 'my-unique-id-001')

  // Add a new chain
  const fs = await import("fs");
  const chain = JSON.parse(fs.readFileSync('./prompt_chain.json', 'utf8'))
  const { data: { chain_id } } = await runner.invoke('create_chain', { chain })

  // Invoke the chain
  const { data: { invocation_id } } = await runner.invoke('run_chain', {
    chain_id,
    inputs: {
      topic: "Food"
    }
  })

  // Check the status. More data is returned; this is just a small fraction.
  for (let i = 0; i < 6; i++) {
    const { data: { state, output } } = await runner.invoke('run_status', { invocation_id })
    console.log(`State: ${state} Output: ${output}`)
    await new Promise(r => setTimeout(r, 500));
  }
}

main().then(() => { }, (e) => {console.log(e)})
```

3. Finally, run `node client.js`