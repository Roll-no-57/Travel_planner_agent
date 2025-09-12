from crewai.flow.flow import Flow, listen, start, and_

class MultiStartFlow(Flow):
    @start()
    def first_method(self):
        print("Running first_method")
        return "Output from first_method"

    @start()
    def another_start(self):
        print("Running another_start")
        return "Output from another_start"

    # This method listens to BOTH starts
    @listen(and_(first_method, another_start))
    def common_listener(self, result):
        print(f"common_listener received: {result}")
        return f"Processed -> {result}"

# Run the flow
flow = MultiStartFlow()
flow.plot("multi_start_flow_plot")
final_output = flow.kickoff()

print("---- Final Output ----")
print(final_output)
